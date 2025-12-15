"""Platform for sensor integration."""
from __future__ import annotations

import logging
import unicodedata
from datetime import timedelta
from typing import Any, Dict

import aiohttp
from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DEFAULT_ICON,
    DOMAIN,
    UNIT_OF_MEASUREMENT,
    ATTRIBUTION,
    CONF_STATIONID)
from .dgeg import DGEG, Station

logger = logging.getLogger(__name__)
logger.level = logging.INFO

# Time between updating data from API
SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_entry(hass: HomeAssistant,
                            config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    session = async_get_clientsession(hass, True)
    api = DGEG(session)

    config = config_entry.data
    station = await api.get_station(config[CONF_STATIONID])

    sensors = [PrecosCombustiveisSensor(
        api,
        config[CONF_STATIONID],
        station,
        fuel["TipoCombustivel"]
    ) for fuel in station.fuels]
    async_add_entities(sensors, update_before_add=True)


class PrecosCombustiveisSensor(SensorEntity):
    """Representation of a PrecosCombustiveis Sensor."""

    def __init__(self, api: DGEG, station_id: int, station: Station, fuel_name: str):
        super().__init__()
        self._api = api
        self._station_id = station_id
        self._station = station
        self._fuel_name = fuel_name

        # Provide name and unique_id via HA entity attributes to avoid overriding cached_property
        self._attr_unique_id = f"{DOMAIN}-{self._station_id}-{self._fuel_name}".lower()
        self._attr_name = f"{self._station.brand} {self._station.name} {self._fuel_name}"
        self._attr_available = True
        self._attr_native_value = None
        self._attr_icon = DEFAULT_ICON
        self._attr_native_unit_of_measurement = UNIT_OF_MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_attribution = ATTRIBUTION
        self._attr_entity_picture = self._get_entity_picture(self._station)
        self._attr_extra_state_attributes = self._build_extra_state_attributes(
            self._station
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._station_id))},
            name=self._station.name,
            model=self._station.brand,
            manufacturer="DGEG",
        )

    def _get_entity_picture(self, station: Station) -> str | None:
        brand = station.brand
        if brand and brand.lower() != "genérico":
            normalized_brand = unicodedata.normalize("NFD", brand.lower())
            brand_name = "".join(c for c in normalized_brand if c.isalpha())
            return f"/local/precoscombustiveis/{brand_name}.png"
        return None

    def _build_extra_state_attributes(self, station: Station) -> Dict[str, Any]:
        return {
            "GasStationId": self._station_id,
            "Brand": station.brand,
            "Name": station.name,
            "Address": station.address,
            "Latitude": station.latitude,
            "Longitude": station.longitude,
            "StationType": station.type,
            "LastPriceUpdate": station.getLastUpdate(self._fuel_name),
        }

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            api = self._api
            gas_station = await api.get_station(self._station_id)
            if gas_station:
                self._attr_native_value = gas_station.getPrice(self._fuel_name)
                self._attr_available = True
        except aiohttp.ClientError as err:
            self._attr_available = False
            logger.exception("Error updating data from DGEG API. %s", err)
