"""DataUpdateCoordinator for PrecosCombustiveis."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .dgeg import DGEG, Station
from .forecast import ForecastClient, ForecastError, FuelForecast
from .const import DOMAIN, FORECAST_UNIQUE_ID

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=60)
FORECAST_UPDATE_INTERVAL = timedelta(hours=6)


class PrecosCombustiveisCoordinator(DataUpdateCoordinator[Station]):
    """Coordinator to manage fetching data from DGEG API."""

    def __init__(self, hass: HomeAssistant, api: DGEG, station_id: int) -> None:
        """Initialize the coordinator."""
        self._api = api
        self._station_id = station_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> Station:
        """Fetch data from DGEG API."""
        try:
            station = await self._api.get_station(self._station_id)
            if station is None:
                raise UpdateFailed("No data returned from DGEG API")
            return station
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with DGEG API: {err}") from err


class ForecastCoordinator(DataUpdateCoordinator[dict[str, FuelForecast]]):
    """Coordinator that fetches the weekly price forecast once for all fuels."""

    def __init__(self, hass: HomeAssistant, client: ForecastClient) -> None:
        """Initialize the coordinator."""
        self._client = client
        super().__init__(
            hass,
            _LOGGER,
            name=FORECAST_UNIQUE_ID,
            update_interval=FORECAST_UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, FuelForecast]:
        """Fetch the forecast from precocombustiveis.pt."""
        try:
            return await self._client.get_forecast()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with precocombustiveis.pt: {err}") from err
        except ForecastError as err:
            raise UpdateFailed(f"Unexpected forecast page: {err}") from err
