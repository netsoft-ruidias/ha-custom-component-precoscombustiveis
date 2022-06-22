"""The PrecosCombustiveis integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .dgeg import DGEG
from .const import DOMAIN

__version__ = "1.1.0"
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Start configuring the API."""
    _LOGGER.debug("Start 'async_setup'...")
    
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass, True)
    api = DGEG(session)

    _LOGGER.debug("Save API in hass.data[DOMAIN]")

    hass.data[DOMAIN] = {"api": api}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the component from a config entry."""
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Unload a config entry."""
#     unload_ok = await hass.config_entries.async_forward_entry_unload(
#         entry, DOMAIN)

#     if unload_ok:
#         for unsub in hass.data[DOMAIN].listeners:
#             unsub()
#         hass.data.pop(DOMAIN)

#         return True

#     return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    # await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)