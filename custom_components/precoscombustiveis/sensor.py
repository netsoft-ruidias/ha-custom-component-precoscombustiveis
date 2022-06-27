"""Platform for sensor integration."""
from __future__ import annotations

import aiohttp
import logging

from datetime import timedelta
from typing import Any, Callable, Dict

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_ICON, 
    DOMAIN, 
    UNIT_OF_MEASUREMENT, 
    ATTRIBUTION, 
    CONF_STATIONID)
from .dgeg import DGEG, Station

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

# Time between updating data from API
SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_entry(hass: HomeAssistant, 
                            config_entry: ConfigEntry, 
                            async_add_entities: Callable):
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
        self._state_class = SensorStateClass.TOTAL
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
    def attribution(self):
        return ATTRIBUTION

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return {
            "Brand": self._station.brand,
            "Name": self._station.name,
            "Address": self._station.address,
            "stationType": self._station.type,
            "lastPriceUpdate": self._station.lastUpdate,
        }

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            api = self._api
            station = await api.getStation(self._stationId)
            if (station):
                fuel = [f for f in self._station.fuels if f["TipoCombustivel"] == self._fuelName][0]
                if (fuel):               
                    self._state = float(fuel["Preco"].replace(" €/litro", "").replace(",", "."))
        except aiohttp.ClientError as err:
            self._available = False
            _LOGGER.exception("Error updating data from DGEG API. %s", err)