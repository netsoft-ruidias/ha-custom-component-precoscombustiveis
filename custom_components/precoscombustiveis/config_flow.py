"""Config flow for PrecosCombustiveis integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for adding a city with multiple gas stations."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize flow."""
        self._stations: list = []
        self._distrito_id: int | None = None
        self._localidade: str | None = None

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

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: Select district."""
        if user_input is None:
            distrito_options = [
                {"value": str(id), "label": name}
                for id, name in sorted(DISTRITOS.items(), key=lambda x: x[1])
            ]

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("distrito_select"): SelectSelector(
                            SelectSelectorConfig(
                                options=distrito_options,
                                mode=SelectSelectorMode.DROPDOWN,
                                sort=True,
                            )
                        )
                    }
                ),
            )

        self._distrito_id = int(user_input["distrito_select"])

        session = async_get_clientsession(self.hass)
        api = DGEG(session)
        self._stations = await api.list_stations(self._distrito_id)

        if not self._stations:
            return self.async_abort(reason="no_stations")

        return await self.async_step_localidade()

    async def async_step_localidade(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2: Select city."""
        if user_input is None:
            localidades = sorted(
                {
                    (station.get("Localidade") or "Desconhecido").strip()
                    for station in self._stations
                }
            )

            existing_cities = {
                entry.data.get(CONF_LOCALIDADE) for entry in self._async_current_entries()
            }
            available_localidades = [loc for loc in localidades if loc not in existing_cities]

            if not available_localidades:
                return self.async_abort(reason="all_cities_configured")

            localidade_options = [
                {"value": loc, "label": f"{loc} ({self._count_stations_in_localidade(loc)} postos)"}
                for loc in available_localidades
            ]

            return self.async_show_form(
                step_id="localidade",
                data_schema=vol.Schema(
                    {
                        vol.Required("localidade_select"): SelectSelector(
                            SelectSelectorConfig(
                                options=localidade_options,
                                mode=SelectSelectorMode.DROPDOWN,
                                sort=True,
                            )
                        )
                    }
                ),
                description_placeholders={
                    "distrito": DISTRITOS[self._distrito_id],
                    "total_stations": str(len(self._get_unique_stations())),
                },
            )

        self._localidade = user_input["localidade_select"]
        return await self.async_step_stations()

    def _count_stations_in_localidade(self, localidade: str) -> int:
        """Count unique stations in a locality."""
        filtered = [
            s
            for s in self._stations
            if (s.get("Localidade") or "Desconhecido").strip() == localidade
        ]
        return len(self._get_unique_stations(filtered))

    async def async_step_stations(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Select multiple stations from the city."""
        if user_input is None:
            filtered = [
                s
                for s in self._stations
                if (s.get("Localidade") or "Desconhecido").strip() == self._localidade
            ]
            unique_stations = self._get_unique_stations(filtered)

            station_options = [
                {
                    "value": str(station["Id"]),
                    "label": f"{station.get('Marca', 'N/A')} - {station.get('Nome', 'N/A')}",
                }
                for station in unique_stations
            ]

            return self.async_show_form(
                step_id="stations",
                data_schema=vol.Schema(
                    {
                        vol.Required("station_select", default=[]): SelectSelector(
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
                    "localidade": self._localidade,
                    "stations_count": str(len(unique_stations)),
                },
            )

        selected_ids = user_input["station_select"]

        if not selected_ids:
            return self.async_abort(reason="no_stations_selected")

        await self.async_set_unique_id(f"{self._distrito_id}_{self._localidade}")
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

        filtered = [
            s for s in all_stations if (s.get("Localidade") or "Desconhecido").strip() == localidade
        ]
        seen_ids: set[str] = set()
        unique_stations = []
        for station in filtered:
            station_id = str(station["Id"])
            if station_id not in seen_ids:
                seen_ids.add(station_id)
                unique_stations.append(station)

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
