"""Platform for sensor integration."""
from __future__ import annotations

import aiohttp
import logging

from datetime import timedelta
from typing import Any, Dict

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_ICON, 
    DOMAIN, 
    UNIT_OF_MEASUREMENT, 
    ATTRIBUTION, 
    CONF_STATIONID)
from .dgeg import DGEG, Station

_LOGGER = logging.getLogger(__name__)

# Time between updating data from API
SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_entry(hass: HomeAssistant, 
                            config_entry: ConfigEntry, 
                            async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    session = async_get_clientsession(hass, True)
    api = DGEG(session)

    config = config_entry.data
    station = await api.getStation(config[CONF_STATIONID])
    
    sensors = [PrecosCombustiveisSensor(
        api, 
        config[CONF_STATIONID], 
        station, 
        fuel["TipoCombustivel"]
    ) for fuel in station.fuels]
    async_add_entities(sensors, update_before_add=True)


class PrecosCombustiveisSensor(SensorEntity):
    """Representation of a PrecosCombustiveis Sensor."""

    def __init__(self, api: DGEG, stationId: float, station: Station, fuelName: str):
        super().__init__()
        self._api = api
        self._stationId = stationId
        self._station = station
        self._fuelName = fuelName
        
        self._icon = DEFAULT_ICON
        self._unit_of_measurement = UNIT_OF_MEASUREMENT
        self._device_class = SensorDeviceClass.MONETARY
        self._state_class = SensorStateClass.MEASUREMENT
        self._state = None
        self._available = True

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._station.brand} {self._station.name} {self._fuelName}"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{DOMAIN}-{self._stationId}-{self._fuelName}".lower()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> float:
        return self._state

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        return self._icon

    @property
    def entity_picture(self):
        """Return the entity picture."""        
        if self._station.brand and self._station.brand.lower() != "genérico":
            return f"/local/precoscombustiveis/{self._station.brand.lower()}.png"
        else:
            return ""

    @property
    def attribution(self):
        return ATTRIBUTION

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return {
            "GasStationId": self._stationId,
            "Brand": self._station.brand,
            "Name": self._station.name,
            "Address": self._station.address,
            "Latitude": self._station.latitude,
            "Longitude": self._station.longitude,
            "StationType": self._station.type,
            "LastPriceUpdate": self._station.getLastUpdate(self._fuelName),
        } 

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            api = self._api
            gasStation = await api.getStation(self._stationId)
            if (gasStation):
                self._state = gasStation.getPrice(self._fuelName)
        except aiohttp.ClientError as err:
            self._available = False
            _LOGGER.exception("Error updating data from DGEG API. %s", err)
