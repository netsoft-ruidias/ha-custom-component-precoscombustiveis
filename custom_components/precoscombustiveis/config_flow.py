"""Config flow for PrecosCombustiveis integration."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_DISTRITO_ID,
    CONF_LOCALIDADE,
    CONF_STATION_IDS,
    DISTRITOS,
    DOMAIN,
)
from .dgeg import DGEG

_LOGGER = logging.getLogger(__name__)


def _normalize_localidade(localidade: str | None) -> str:
    """Normalize a localidade string for consistent comparison.

    Removes accents, converts to lowercase, and normalizes whitespace.
    Examples: "TÁBUA", "Tábua", "tábua", "TABUA" -> "tabua"
    """
    if not localidade:
        return "desconhecido"
    # Strip whitespace first
    text = localidade.strip()
    # Normalize to NFD (decomposed form) to separate base chars from combining marks
    text = unicodedata.normalize("NFD", text)
    # Remove combining marks (accents)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Convert to lowercase
    text = text.lower()
    # Replace multiple spaces with single space
    return " ".join(text.split())


def _get_display_localidade(localidade: str | None) -> str:
    """Get display-friendly localidade (preserves original casing, just strips)."""
    if not localidade:
        return "Desconhecido"
    return localidade.strip()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for adding a city with multiple gas stations."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize flow."""
        self._stations: list = []
        self._distrito_id: int | None = None
        self._localidade: str | None = None
        self._localidade_normalized: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    def _get_unique_stations(self, stations: list | None = None) -> list:
        """Get unique stations by ID."""
        source = stations if stations is not None else self._stations
        seen_ids: set[str] = set()
        unique = []
        for station in source:
            station_id = str(station["Id"])
            if station_id not in seen_ids:
                seen_ids.add(station_id)
                unique.append(station)
        return unique

    def _get_stations_for_localidade(self, localidade_normalized: str) -> list:
        """Get all stations matching a normalized localidade."""
        return [
            s
            for s in self._stations
            if _normalize_localidade(s.get("Localidade")) == localidade_normalized
        ]

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: Choose method - by location or by station ID."""
        if user_input is None:
            method_options = [
                {"value": "by_location", "label": "🔍 Pesquisar por localidade"},
                {"value": "by_id", "label": "🔢 Adicionar por ID da estação"},
            ]

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("method"): SelectSelector(
                            SelectSelectorConfig(
                                options=method_options,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    }
                ),
            )

        if user_input["method"] == "by_id":
            return await self.async_step_station_id()

        return await self.async_step_distrito()

    async def async_step_distrito(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2a: Select district (when searching by location)."""
        # Handle back navigation
        if user_input is not None and user_input.get("distrito_select") == "__back__":
            return await self.async_step_user()

        if user_input is None:
            distrito_options = [{"value": "__back__", "label": "← Voltar"}]
            distrito_options.extend(
                [
                    {"value": str(id), "label": name}
                    for id, name in sorted(DISTRITOS.items(), key=lambda x: x[1])
                ]
            )

            return self.async_show_form(
                step_id="distrito",
                data_schema=vol.Schema(
                    {
                        vol.Required("distrito_select"): SelectSelector(
                            SelectSelectorConfig(
                                options=distrito_options,
                                mode=SelectSelectorMode.DROPDOWN,
                                sort=False,
                            )
                        )
                    }
                ),
            )

        self._distrito_id = int(user_input["distrito_select"])

        session = async_get_clientsession(self.hass)
        api = DGEG(session)
        self._stations = await api.list_stations(self._distrito_id)

        _LOGGER.debug(
            "Fetched %d stations for distrito %s (%s)",
            len(self._stations),
            self._distrito_id,
            DISTRITOS.get(self._distrito_id, "Unknown"),
        )

        if not self._stations:
            return self.async_abort(reason="no_stations")

        return await self.async_step_localidade()

    async def async_step_station_id(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2b: Enter station ID directly."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input.get("station_id", "").strip()

            if not station_id:
                errors["station_id"] = "invalid_station_id"
            else:
                # Validate the station ID by fetching it
                session = async_get_clientsession(self.hass)
                api = DGEG(session)

                try:
                    station = await api.getStation(station_id)
                    if station and station.name:
                        # Create entry with this single station
                        await self.async_set_unique_id(f"station_{station_id}")
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"{station.name}",
                            data={
                                CONF_DISTRITO_ID: 0,  # Unknown distrito
                                CONF_LOCALIDADE: station.name,
                                CONF_STATION_IDS: [station_id],
                            },
                        )
                    else:
                        errors["station_id"] = "station_not_found"
                except AbortFlow:
                    # Re-raise AbortFlow exceptions (like already_configured)
                    raise
                except Exception:
                    errors["station_id"] = "station_not_found"

        return self.async_show_form(
            step_id="station_id",
            data_schema=vol.Schema(
                {
                    vol.Required("station_id"): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_localidade(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Select city."""
        # Handle back navigation
        if user_input is not None and user_input.get("localidade_select") == "__back__":
            self._distrito_id = None
            self._stations = []
            return await self.async_step_distrito()

        if user_input is None:
            # Build map of normalized localidade -> display name
            localidade_map: dict[str, str] = {}
            for station in self._stations:
                raw = station.get("Localidade")
                normalized = _normalize_localidade(raw)
                display = _get_display_localidade(raw)
                # Keep the first display name we find for each normalized version
                if normalized not in localidade_map:
                    localidade_map[normalized] = display

            # Get existing entries using normalized comparison
            existing_normalized = {
                _normalize_localidade(entry.data.get(CONF_LOCALIDADE))
                for entry in self._async_current_entries()
            }

            available_localidades = [
                (norm, disp)
                for norm, disp in sorted(localidade_map.items(), key=lambda x: x[1])
                if norm not in existing_normalized
            ]

            if not available_localidades:
                return self.async_abort(reason="all_cities_configured")

            # Add back option at the beginning
            localidade_options = [
                {"value": "__back__", "label": "← Voltar (escolher outro distrito)"}
            ]
            localidade_options.extend(
                [
                    {
                        "value": norm,
                        "label": f"{disp} ({self._count_stations_in_localidade(norm)} postos)",
                    }
                    for norm, disp in available_localidades
                ]
            )

            _LOGGER.debug(
                "Available localidades for distrito %s: %d cities with stations",
                DISTRITOS.get(self._distrito_id, "Unknown"),
                len(localidade_options) - 1,  # -1 for back option
            )

            return self.async_show_form(
                step_id="localidade",
                data_schema=vol.Schema(
                    {
                        vol.Required("localidade_select"): SelectSelector(
                            SelectSelectorConfig(
                                options=localidade_options,
                                mode=SelectSelectorMode.DROPDOWN,
                                sort=False,  # Don't sort to keep back at top
                            )
                        )
                    }
                ),
                description_placeholders={
                    "distrito": DISTRITOS[self._distrito_id],
                    "total_stations": str(len(self._get_unique_stations())),
                },
                last_step=False,
            )

        # Store both normalized (for matching) and find display name
        self._localidade_normalized = user_input["localidade_select"]

        # Find the display name for this normalized localidade
        for station in self._stations:
            if _normalize_localidade(station.get("Localidade")) == self._localidade_normalized:
                self._localidade = _get_display_localidade(station.get("Localidade"))
                break

        _LOGGER.debug(
            "Selected localidade: %s (normalized: %s)",
            self._localidade,
            self._localidade_normalized,
        )

        return await self.async_step_stations()

    def _count_stations_in_localidade(self, localidade_normalized: str) -> int:
        """Count unique stations in a locality using normalized comparison."""
        filtered = self._get_stations_for_localidade(localidade_normalized)
        count = len(self._get_unique_stations(filtered))
        _LOGGER.debug(
            "Localidade '%s' has %d unique stations (from %d total matches)",
            localidade_normalized,
            count,
            len(filtered),
        )
        return count

    async def async_step_stations(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Select multiple stations from the city."""
        # Handle back navigation - check if only "__back__" is selected
        if user_input is not None:
            selected = user_input.get("station_select", [])
            if "__back__" in selected:
                self._localidade = None
                self._localidade_normalized = None
                return await self.async_step_localidade()

        if user_input is None:
            filtered = self._get_stations_for_localidade(self._localidade_normalized)
            unique_stations = self._get_unique_stations(filtered)

            _LOGGER.debug(
                "Found %d unique stations for localidade '%s' (filtered from %d)",
                len(unique_stations),
                self._localidade,
                len(filtered),
            )

            # Add back option at the beginning
            station_options = [{"value": "__back__", "label": "← Voltar (escolher outra cidade)"}]
            station_options.extend(
                [
                    {
                        "value": str(station["Id"]),
                        "label": f"{station.get('Marca', 'N/A')} - {station.get('Nome', 'N/A')}",
                    }
                    for station in unique_stations
                ]
            )

            return self.async_show_form(
                step_id="stations",
                data_schema=vol.Schema(
                    {
                        vol.Required("station_select", default=[]): SelectSelector(
                            SelectSelectorConfig(
                                options=station_options,
                                mode=SelectSelectorMode.DROPDOWN,
                                multiple=True,
                                sort=False,  # Don't sort to keep back at top
                            )
                        )
                    }
                ),
                description_placeholders={
                    "localidade": self._localidade,
                    "stations_count": str(len(unique_stations)),
                },
                last_step=True,
            )

        selected_ids = user_input["station_select"]
        # Remove back option if somehow included
        selected_ids = [sid for sid in selected_ids if sid != "__back__"]

        if not selected_ids:
            return self.async_abort(reason="no_stations_selected")

        await self.async_set_unique_id(f"{self._distrito_id}_{self._localidade_normalized}")
        self._abort_if_unique_id_configured()

        distrito_name = DISTRITOS.get(self._distrito_id, "Portugal")

        return self.async_create_entry(
            title=f"{self._localidade}, {distrito_name}",
            data={
                CONF_DISTRITO_ID: self._distrito_id,
                CONF_LOCALIDADE: self._localidade,
                CONF_STATION_IDS: selected_ids,
            },
        )


class OptionsFlowHandler(OptionsFlow):
    """Options flow to add/remove stations from a city."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._stations: list = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options - add or remove stations."""
        if user_input is not None:
            new_station_ids = user_input.get("station_select", [])

            if not new_station_ids:
                return self.async_abort(reason="no_stations_selected")

            new_data = {**self._config_entry.data, CONF_STATION_IDS: new_station_ids}
            self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)

            return self.async_create_entry(title="", data={})

        distrito_id = self._config_entry.data.get(CONF_DISTRITO_ID)
        localidade = self._config_entry.data.get(CONF_LOCALIDADE)
        current_ids = self._config_entry.data.get(CONF_STATION_IDS, [])

        session = async_get_clientsession(self.hass)
        api = DGEG(session)
        all_stations = await api.list_stations(distrito_id)

        # Use normalized comparison to find all stations for this localidade
        localidade_normalized = _normalize_localidade(localidade)

        filtered = [
            s
            for s in all_stations
            if _normalize_localidade(s.get("Localidade")) == localidade_normalized
        ]

        seen_ids: set[str] = set()
        unique_stations = []
        for station in filtered:
            station_id = str(station["Id"])
            if station_id not in seen_ids:
                seen_ids.add(station_id)
                unique_stations.append(station)

        _LOGGER.debug(
            "Options flow: Found %d unique stations for localidade '%s' (normalized: '%s')",
            len(unique_stations),
            localidade,
            localidade_normalized,
        )

        station_options = [
            {
                "value": str(station["Id"]),
                "label": f"{station.get('Marca', 'N/A')} - {station.get('Nome', 'N/A')}",
            }
            for station in unique_stations
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("station_select", default=current_ids): SelectSelector(
                        SelectSelectorConfig(
                            options=station_options,
                            mode=SelectSelectorMode.DROPDOWN,
                            multiple=True,
                            sort=True,
                        )
                    )
                }
            ),
            description_placeholders={
                "localidade": localidade,
                "current_count": str(len(current_ids)),
                "available_count": str(len(unique_stations)),
            },
        )
