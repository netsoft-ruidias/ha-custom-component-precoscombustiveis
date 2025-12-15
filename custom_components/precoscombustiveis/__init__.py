"""The PrecosCombustiveis integration."""

from __future__ import annotations

import logging
import os
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DISTRITO_ID,
    CONF_LOCALIDADE,
    CONF_STATION_IDS,
    CONF_STATION_NAME,
    CONF_STATIONID,
    DOMAIN,
)
from .coordinator import PrecosCombustiveisCoordinator
from .dgeg import DGEG

__version__ = "3.0.0"
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to new format."""
    if config_entry.version == 1:
        _LOGGER.info("Migrating config entry %s from version 1 to 2", config_entry.title)

        old_data = dict(config_entry.data)
        old_station_id = old_data.get(CONF_STATIONID)
        old_station_name = old_data.get(CONF_STATION_NAME, "Migrated Station")

        if old_station_id:
            new_data = {
                CONF_DISTRITO_ID: 0,
                CONF_LOCALIDADE: old_station_name,
                CONF_STATION_IDS: [str(old_station_id)],
            }

            hass.config_entries.async_update_entry(
                config_entry,
                data=new_data,
                title=f"{old_station_name} (Migrado)",
                version=2,
            )
            _LOGGER.info(
                "Successfully migrated entry %s with station %s",
                config_entry.entry_id,
                old_station_id,
            )
            return True

        _LOGGER.error("Failed to migrate entry %s: no station ID found", config_entry.entry_id)
        return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PrecosCombustiveis from a config entry."""
    await copy_images_to_www(hass)

    station_ids = entry.data.get(CONF_STATION_IDS, [])

    if not station_ids:
        _LOGGER.error("No station IDs found in config entry")
        return False

    session = async_get_clientsession(hass, verify_ssl=False)
    api = DGEG(session)

    coordinators: dict[str, PrecosCombustiveisCoordinator] = {}

    for station_id in station_ids:
        coordinator = PrecosCombustiveisCoordinator(
            hass=hass,
            config_entry=entry,
            api=api,
            station_id=station_id,
            station_name=f"Station {station_id}",
        )

        await coordinator.async_config_entry_first_refresh()
        coordinators[station_id] = coordinator

        _LOGGER.debug("Created coordinator for station %s", station_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def copy_images_to_www(hass: HomeAssistant) -> None:
    """Copy brand images to the www folder for entity pictures."""
    source_dir = os.path.join(os.path.dirname(__file__), "images")
    target_dir = hass.config.path("www", "precoscombustiveis")

    try:
        os.makedirs(target_dir, exist_ok=True)
        filenames = await hass.async_add_executor_job(os.listdir, source_dir)

        for filename in filenames:
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_dir, filename)

            if not os.path.exists(target_file):
                await hass.async_add_executor_job(shutil.copy, source_file, target_file)
                _LOGGER.info("Copied brand image: %s", filename)

    except Exception as err:
        _LOGGER.error("Error copying brand images: %s", err)
