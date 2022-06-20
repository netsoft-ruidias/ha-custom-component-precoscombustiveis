"""Config flow for PrecosCombustiveis integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

DATA_SCHEMA = vol.Schema(
    { 
        vol.Required("stationId"): str
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
            await self.async_set_unique_id(user_input["stationId"].lower())
            self._abort_if_unique_id_configured()

            _LOGGER.debug("Config is valid!")
            return self.async_create_entry(
                title="DGEG " + user_input["stationId"], 
                data = user_input
            ) 

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors,
        )