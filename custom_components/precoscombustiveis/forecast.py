"""Weekly fuel price forecast, scraped from precocombustiveis.pt."""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

import aiohttp

from .const import FORECAST_URL

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}

TREND_UP = "sobe"
TREND_DOWN = "desce"
TREND_NEUTRAL = "neutro"

LEVEL_NONE = "nula"
LEVEL_SLIGHT = "ligeira"
LEVEL_MODERATE = "moderada"
LEVEL_STRONG = "forte"

_TITLE_SUFFIX = "sobe ou desce na proxima semana"
_SECTION_RE = re.compile(r"<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>", re.S | re.I)
_TIME_RE = re.compile(r"<time[^>]*\bdatetime=[\"'](\d{4}-\d{2}-\d{2})", re.I)
_VALUE_RE = re.compile(r"([+\-−–]?)\s*(\d+(?:[.,]\d+)?)\s*€\s*/\s*l\b", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_UP_WORDS = ("subir", "subida", "sobe", "aumento")
_DOWN_WORDS = ("descer", "descida", "desce", "diminuicao")


class ForecastError(Exception):
    """Raised when the forecast page cannot be understood."""


@dataclass(frozen=True)
class FuelForecast:
    """Weekly forecast for a single fuel."""

    variation: float  # €/L, positive = rise, negative = fall
    trend: str
    level: str
    formatted: str
    start: str  # ISO date of the forecast week's Monday
    end: str  # ISO date of the forecast week's Sunday
    last_update: str  # ISO date the source page was updated


def _normalize(text: str) -> str:
    """Lowercase and strip accents."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _clean(fragment: str) -> str:
    """Strip tags/entities and collapse whitespace."""
    text = html.unescape(_TAG_RE.sub(" ", fragment))
    return re.sub(r"\s+", " ", text).strip()


def _parse_variation(text: str) -> Decimal:
    """Extract the signed €/L variation from a forecast paragraph."""
    match = _VALUE_RE.search(text)
    if match is None:
        # Section present but without a value: the page says there is no change.
        return Decimal(0)

    sign, number = match.groups()
    value = Decimal(number.replace(",", "."))
    if sign in ("-", "−", "–"):
        return -value
    if sign == "+":
        return value

    words = _normalize(text)
    if any(w in words for w in _DOWN_WORDS) and not any(w in words for w in _UP_WORDS):
        return -value
    return value


def calc_trend(variation: Decimal) -> str:
    """Return the trend for a variation."""
    if variation > 0:
        return TREND_UP
    if variation < 0:
        return TREND_DOWN
    return TREND_NEUTRAL


def calc_level(variation: Decimal) -> str:
    """Return the variation level, based on the absolute value in cents."""
    cents = abs(variation) * 100
    if cents == 0:
        return LEVEL_NONE
    if cents < 2:
        return LEVEL_SLIGHT
    if cents < 6:
        return LEVEL_MODERATE
    return LEVEL_STRONG


def format_variation(variation: Decimal) -> str:
    """Format a €/L variation as e.g. '+ 6 cent€/Lt' or '- 4,5 cent€/Lt'."""
    cents = abs(variation) * 100
    number = f"{cents:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    if variation > 0:
        return f"+ {number} cent€/Lt"
    if variation < 0:
        return f"- {number} cent€/Lt"
    return "0 cent€/Lt"


def calc_week(updated: date) -> tuple[date, date]:
    """Return the Monday and Sunday of the week forecast by a page update date."""
    monday = updated + timedelta(days=(7 - updated.weekday()) % 7)
    return monday, monday + timedelta(days=6)


def parse_forecast(page: str) -> dict[str, FuelForecast]:
    """Parse the forecast page into a forecast per fuel key (see FORECAST_FUELS)."""
    time_match = _TIME_RE.search(page)
    if time_match is None:
        raise ForecastError("Update date not found in forecast page")
    updated = datetime.strptime(time_match.group(1), "%Y-%m-%d").date()
    start, end = calc_week(updated)

    forecasts: dict[str, FuelForecast] = {}
    for title_html, text_html in _SECTION_RE.findall(page):
        title = _normalize(_clean(title_html))
        if not title.endswith(_TITLE_SUFFIX):
            continue

        for fuel in ("gasoleo", "gasolina"):
            if fuel in title and fuel not in forecasts:
                variation = _parse_variation(_clean(text_html))
                forecasts[fuel] = FuelForecast(
                    variation=float(variation),
                    trend=calc_trend(variation),
                    level=calc_level(variation),
                    formatted=format_variation(variation),
                    start=start.isoformat(),
                    end=end.isoformat(),
                    last_update=updated.isoformat(),
                )

    if not forecasts:
        raise ForecastError("No fuel forecast found in forecast page")
    return forecasts


class ForecastClient:
    """Fetches the weekly forecast from precocombustiveis.pt."""

    def __init__(self, websession: aiohttp.ClientSession) -> None:
        self.websession = websession

    async def get_forecast(self) -> dict[str, FuelForecast]:
        """Fetch and parse the forecast page."""
        async with self.websession.get(
            FORECAST_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
        ) as res:
            res.raise_for_status()
            return parse_forecast(await res.text())
