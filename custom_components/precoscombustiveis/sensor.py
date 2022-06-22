"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_ICON, DOMAIN, UNIT_OF_MEASUREMENT
from .dgeg import DGEG, Station

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup_entry(hass: HomeAssistant, 
                            config_entry: ConfigEntry, 
                            async_add_entities):
    """Setup sensor platform."""
    session = async_get_clientsession(hass, True)
    api = DGEG(session)

    config = config_entry.data
    station = await api.getStation(config["stationId"])

    sensors = [PrecosCombustiveisSensor(api, config["stationId"], station, fuel["TipoCombustivel"]) for fuel in station.fuels]
    async_add_entities(sensors)


class PrecosCombustiveisSensor(SensorEntity):
    """Representation of a PrecosCombustiveis Sensor."""

    def __init__(self, api: DGEG, stationId: float, station: Station, fuelName: str):
        super().__init__()
        self._api = api
        self._stationId = stationId
        self._station = station
        self._fuelName = fuelName
        self._state = 0
        self._icon = DEFAULT_ICON
        self._unit_of_measurement = UNIT_OF_MEASUREMENT
        self._device_class = SensorDeviceClass.MONETARY
        self._state_class = SensorStateClass.TOTAL

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._station.brand} {self._station.name} {self._fuelName}"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{DOMAIN}-{self._stationId}-{self._fuelName}".lower()

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
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "brand": self._station.brand,
            "Name": self._station.name,
            "stationType": self._station.type,
            "lastUpdate": self._station.lastUpdate,
        }

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        api = self._api
        station = await api.getStation(self._stationId)
        if (station):
            fuel = [f for f in self._station.fuels if f["TipoCombustivel"] == self._fuelName][0]
            if (fuel):               
                self._state = float(fuel["Preco"].replace(" €/litro", "").replace(",", "."))