"""Config flow for PrecosCombustiveis integration."""
from __future__ import annotations
from typing import Any, Dict, Optional
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_STATIONID,
    CONF_STATION_NAME,
    CONF_STATION_BRAND,
    CONF_STATION_ADDRESS,
    CONF_FUEL_TYPES,
    DISTRITOS
)
from .dgeg import DGEG

logger = logging.getLogger(__name__)
logger.level = logging.INFO

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATIONID): str
    }
)

class PrecosCombustiveisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """PrecosCombustiveis config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @classmethod
    def async_supports_options_flow(cls, config_entry):
        """Return options flow support for this config entry."""
        return True

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow for this handler."""
        return PrecosCombustiveisOptionsFlow()

    def is_matching(self, other_flow):
        """Return True if the config matches the integration."""
        # Prevent duplicate entries for the same station
        if self.context.get("source") == config_entries.SOURCE_USER:
            # Check if another flow is already configuring the same station
            return (
                other_flow.context.get("source") == config_entries.SOURCE_USER
                and other_flow.init_data.get(CONF_STATIONID)
                == self.context.get(CONF_STATIONID)
            )
        return False

    def __init__(self):
        """Initialize flow."""
        self._stations: list = []
        self._municipio_stations: list = []
        self._filtered_stations: list = []
        self._selected_station: Dict[str, Any] = {}
        self._selected_municipio: str = ""
        self._selected_brand: str = ""
        self._selected_fuel_types: list = []
        self._distrito_id: int = 0

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle the initial step - select distrito."""
        if user_input is None:
            # Create distrito selection list
            distritos_list = {
                str(id): name for id, name in DISTRITOS.items()
            }

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("distrito_select"): vol.In(distritos_list)
                })
            )

        # Store selected distrito and fetch stations once
        self._distrito_id = int(user_input["distrito_select"])
        session = async_get_clientsession(self.hass)
        api = DGEG(session)
        self._stations = await api.list_stations(self._distrito_id)

        if not self._stations:
            return self.async_abort(reason="no_stations")

        return await self.async_step_municipio()

    async def async_step_municipio(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle municipio selection for selected distrito."""
        if user_input is None:
            if not self._stations:
                return self.async_abort(reason="no_stations")

            municipios = sorted(
                {
                    str(station["Municipio"]).strip()
                    for station in self._stations
                    if station.get("Municipio") and str(station["Municipio"]).strip()
                },
                key=str.casefold,
            )

            if not municipios:
                return self.async_abort(reason="no_stations")

            return self.async_show_form(
                step_id="municipio",
                data_schema=vol.Schema({
                    vol.Required("municipio_select"): vol.In(municipios)
                }),
                description_placeholders={
                    "municipios_count": str(len(municipios)),
                    "distrito": DISTRITOS[self._distrito_id],
                },
            )

        self._selected_municipio = user_input["municipio_select"]
        self._municipio_stations = [
            station
            for station in self._stations
            if str(station.get("Municipio", "")).strip() == self._selected_municipio
        ]

        if not self._municipio_stations:
            return self.async_abort(reason="no_stations")

        return await self.async_step_brand()

    async def async_step_brand(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle brand selection for selected municipio."""
        if user_input is None:
            if not self._municipio_stations:
                return self.async_abort(reason="no_stations")

            # Build sorted unique brands list
            brands = sorted(
                {
                    station["Marca"].strip()
                    for station in self._municipio_stations
                    if station.get("Marca") and str(station["Marca"]).strip()
                },
                key=str.casefold,
            )

            if not brands:
                return self.async_abort(reason="no_brands")

            return self.async_show_form(
                step_id="brand",
                data_schema=vol.Schema({
                    vol.Required("brand_select"): vol.In(brands)
                }),
                description_placeholders={
                    "brands_count": str(len(brands)),
                    "distrito": DISTRITOS[self._distrito_id],
                    "municipio": self._selected_municipio,
                }
            )

        self._selected_brand = user_input["brand_select"]
        self._filtered_stations = [
            station
            for station in self._municipio_stations
            if str(station.get("Marca", "")).strip() == self._selected_brand
        ]

        if not self._filtered_stations:
            return self.async_abort(reason="no_stations")

        return await self.async_step_station()

    async def async_step_station(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle station selection."""
        if user_input is None:
            if not self._filtered_stations:
                return self.async_abort(reason="no_stations")

            # Create filtered selection list for selected brand
            stations_list = {
                str(station["Id"]): (
                    f"{station['Nome']}"
                    if (
                        station["Municipio"] == station["Localidade"]
                        or str(station["Localidade"]).casefold() in str(station["Nome"]).casefold()
                    )
                    else f"[{station['Localidade']}] {station['Nome']}"
                )
                for station in self._filtered_stations
            }

            return self.async_show_form(
                step_id="station",
                data_schema=vol.Schema({
                    vol.Required("station_select"): vol.In(stations_list)
                }),
                description_placeholders={
                    "stations_count": str(len(stations_list)),
                    "distrito": DISTRITOS[self._distrito_id],
                    "municipio": self._selected_municipio,
                    "brand": self._selected_brand,
                }
            )

        # Store selected station details
        station_id = user_input["station_select"]
        selected_station = next(
            (station for station in self._filtered_stations if str(station["Id"]) == station_id),
            None
        )

        if not selected_station:
            return self.async_abort(reason="station_not_found")

        self._selected_station = {
            CONF_STATIONID: str(selected_station["Id"]),
            CONF_STATION_NAME: selected_station["Nome"],
            CONF_STATION_BRAND: selected_station["Marca"],
            CONF_STATION_ADDRESS: selected_station["Morada"]
                if selected_station["Localidade"] == self._selected_municipio
                else f"{selected_station['Morada']} - {selected_station['Localidade']}",
        }

        return await self.async_step_fuel_types()

    async def async_step_fuel_types(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle fuel types selection."""
        if user_input is None:
            # Get available fuel types from the selected station
            session = async_get_clientsession(self.hass)
            api = DGEG(session)
            station = await api.get_station(int(self._selected_station[CONF_STATIONID]))

            fuel_types = [fuel["TipoCombustivel"] for fuel in station.fuels]

            if not fuel_types:
                return self.async_abort(reason="no_fuels")

            # Create checkboxes for fuel types
            return self.async_show_form(
                step_id="fuel_types",
                data_schema=vol.Schema({
                    vol.Required("fuel_types_select"): cv.multi_select(fuel_types)
                }),
                description_placeholders={
                    "station_name": self._selected_station[CONF_STATION_NAME],
                    "brand": self._selected_station[CONF_STATION_BRAND],
                    "fuels_count": str(len(fuel_types)),
                },
            )

        # Validate that at least one fuel type is selected
        selected_fuels = user_input.get("fuel_types_select", [])
        if not selected_fuels:
            session = async_get_clientsession(self.hass)
            api = DGEG(session)
            station = await api.get_station(int(self._selected_station[CONF_STATIONID]))
            fuel_types = [fuel["TipoCombustivel"] for fuel in station.fuels]

            return self.async_show_form(
                step_id="fuel_types",
                data_schema=vol.Schema({
                    vol.Required("fuel_types_select"): cv.multi_select(fuel_types)
                }),
                errors={"base": "no_fuel_selected"},
            )

        self._selected_fuel_types = selected_fuels
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Confirm the station selection."""
        if user_input is None:
            # Format selected fuel types as comma-separated string
            fuel_types_str = ", ".join(self._selected_fuel_types)
            
            return self.async_show_form(
                step_id="confirm",
                description_placeholders={
                    "name": self._selected_station[CONF_STATION_NAME],
                    "brand": self._selected_station[CONF_STATION_BRAND],
                    "address": self._selected_station[CONF_STATION_ADDRESS],
                    "distrito": DISTRITOS[self._distrito_id],
                    "municipio": self._selected_municipio,
                    "fuel_types": fuel_types_str,
                }
            )

        # Store selected fuel types
        self._selected_station[CONF_FUEL_TYPES] = self._selected_fuel_types

        # Ensure each station has its own unique config entry (and therefore a device)
        await self.async_set_unique_id(str(self._selected_station[CONF_STATIONID]))
        self._abort_if_unique_id_configured()

        # Create the config entry
        return self.async_create_entry(
            title=f"{self._selected_station[CONF_STATION_NAME]} - {self._selected_station[CONF_STATION_BRAND]}",
            data=self._selected_station,
        )

class PrecosCombustiveisOptionsFlow(config_entries.OptionsFlow):
    """Options flow for PrecosCombustiveis integration."""

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Any:
        """Handle options flow initial step."""
        # Redirect to fuel_types step
        return await self.async_step_fuel_types(user_input)

    async def async_step_fuel_types(self, user_input: Optional[Dict[str, Any]] = None) -> Any:
        """Handle fuel types selection."""
        if user_input is None:
            # Initialize instance variables
            current_fuel_types = self.config_entry.data.get(CONF_FUEL_TYPES, [])
            
            # Get available fuel types from the station
            session = async_get_clientsession(self.hass)
            api = DGEG(session)
            station_id = self.config_entry.data[CONF_STATIONID]
            station = await api.get_station(int(station_id))

            available_fuel_types = [fuel["TipoCombustivel"] for fuel in station.fuels]

            if not available_fuel_types:
                return self.async_abort(reason="no_fuels")

            # Create multi-select for fuel types with currently selected ones as defaults
            return self.async_show_form(
                step_id="fuel_types",
                data_schema=vol.Schema({
                    vol.Required(
                        "fuel_types_select",
                        default=current_fuel_types
                    ): cv.multi_select(available_fuel_types)
                }),
                description_placeholders={
                    "station_name": self.config_entry.data[CONF_STATION_NAME],
                    "brand": self.config_entry.data[CONF_STATION_BRAND],
                    "fuels_count": str(len(available_fuel_types)),
                },
            )

        # Validate that at least one fuel type is selected
        selected_fuels = user_input.get("fuel_types_select", [])
        if not selected_fuels:
            # Re-fetch data if validation fails
            current_fuel_types = self.config_entry.data.get(CONF_FUEL_TYPES, [])
            session = async_get_clientsession(self.hass)
            api = DGEG(session)
            station_id = self.config_entry.data[CONF_STATIONID]
            station = await api.get_station(int(station_id))
            available_fuel_types = [fuel["TipoCombustivel"] for fuel in station.fuels]
            
            return self.async_show_form(
                step_id="fuel_types",
                data_schema=vol.Schema({
                    vol.Required(
                        "fuel_types_select",
                        default=current_fuel_types
                    ): cv.multi_select(available_fuel_types)
                }),
                errors={"base": "no_fuel_selected"},
            )

        # Update the config entry data with new fuel types
        new_data = self.config_entry.data.copy()
        new_data[CONF_FUEL_TYPES] = selected_fuels

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )

        # Reload the config entry to apply changes
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        return self.async_abort(reason="options_updated")