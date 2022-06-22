"""Config flow for PrecosCombustiveis integration."""
from __future__ import annotations

import logging
import voluptuous as vol
import async_timeout

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .dgeg import DGEG
from .const import DOMAIN, FIELD_ID

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

DATA_SCHEMA = vol.Schema(
    { 
        vol.Required(FIELD_ID): str
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """PrecosCombustiveis config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user interface."""
        _LOGGER.debug("Starting async_step_user...")
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[FIELD_ID].lower())
            self._abort_if_unique_id_configured()

            if self._test_gas_station(user_input[FIELD_ID]):
                _LOGGER.debug("Config is valid!")
                return self.async_create_entry(
                    title="DGEG " + user_input[FIELD_ID], 
                    data=user_input
                ) 
            else:
                errors = {"base": "invalid_station"}

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors,
        )
    
    async def _test_gas_station(self, stationId):
        """Return true if gas station exists."""
        session = async_get_clientsession(self.hass, True)
        async with async_timeout.timeout(10):
            api = DGEG(session)
            return await api.testStation(stationId)
