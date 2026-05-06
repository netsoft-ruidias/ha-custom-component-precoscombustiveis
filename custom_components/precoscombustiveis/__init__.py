"""The PrecosCombustiveis integration."""
from __future__ import annotations
import os
import shutil
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .dgeg import DGEG
from .const import DOMAIN

__version__ = "2.0.0"
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Start configuring the API."""
    _LOGGER.debug("Start 'async_setup'...")
    
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass, True)
    api = DGEG(session)

    _LOGGER.debug("Save API in hass.data[DOMAIN]")

    hass.data[DOMAIN] = {"api": api}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the component from a config entry."""
    await copy_images_to_www(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def copy_images_to_www(hass: HomeAssistant):
    """Copy images from the custom component's directory to the www folder."""
    source_dir = os.path.join(os.path.dirname(__file__), "images")
    target_dir = hass.config.path("www", "precoscombustiveis")

    try:
        os.makedirs(target_dir, exist_ok=True)

        # Use async_add_executor_job to avoid blocking the event loop
        filenames = await hass.async_add_executor_job(os.listdir, source_dir)

        for filename in filenames:
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_dir, filename)

            # Copy only if file does not exist or is different (upgrade)
            if not os.path.exists(target_file):
                await hass.async_add_executor_job(shutil.copy, source_file, target_file)
                _LOGGER.info("Copied: %s", filename)
            else:
                _LOGGER.debug("Ignored (because it already exists): %s", filename)

    except Exception as e:
        _LOGGER.error("Error copying images: %s", e)
