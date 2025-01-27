"""Config flow for PrecosCombustiveis integration."""
from __future__ import annotations
from typing import Any, Dict, Optional
import voluptuous as vol

import logging
import async_timeout

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_STATIONID,
    CONF_STATION_NAME,
    CONF_STATION_BRAND,
    CONF_STATION_ADDRESS,
)
from .dgeg import DGEG

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

DATA_SCHEMA = vol.Schema(
    { 
        vol.Required(CONF_STATIONID): str
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """PrecosCombustiveis config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._stations: list = []
        self._selected_station: Dict[str, Any] = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            # Fetch stations list
            session = async_get_clientsession(self.hass)
            api = DGEG(session)
            self._stations = await api.list_stations()

            if not self._stations:
                return self.async_abort(reason="no_stations")

            # Create selection list
            stations_list = {
                str(station["Id"]): f"{station['Distrito']}/{station['Localidade']}: {station['Marca']} - {station['Nome']}"
                for station in self._stations
            }

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("station_select"): vol.In(stations_list)
                }),
                description_placeholders={
                    "stations_count": str(len(self._stations))
                }
            )

        # Store selected station details
        station_id = user_input["station_select"]
        selected_station = next(
            (station for station in self._stations if str(station["Id"]) == station_id),
            None
        )

        if not selected_station:
            return self.async_abort(reason="station_not_found")

        self._selected_station = {
            CONF_STATIONID: str(selected_station["Id"]),
            CONF_STATION_NAME: selected_station["Nome"],
            CONF_STATION_BRAND: selected_station["Marca"],
            CONF_STATION_ADDRESS: selected_station["Morada"],
        }

        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Confirm the station selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="confirm",
                description_placeholders={
                    "name": self._selected_station[CONF_STATION_NAME],
                    "brand": self._selected_station[CONF_STATION_BRAND],
                    "address": self._selected_station[CONF_STATION_ADDRESS],
                }
            )

        # Create the config entry
        return self.async_create_entry(
            title=f"{self._selected_station[CONF_STATION_NAME]} - {self._selected_station[CONF_STATION_BRAND]}",
            data=self._selected_station,
        )

