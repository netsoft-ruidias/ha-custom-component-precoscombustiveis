"""Platform for sensor integration."""
from __future__ import annotations

import logging
import unicodedata


from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_ICON,
    DOMAIN,
    UNIT_OF_MEASUREMENT,
    ATTRIBUTION,
    CONF_STATIONID,
    CONF_FUEL_TYPES)
from .coordinator import PrecosCombustiveisCoordinator
from .dgeg import Station

logger = logging.getLogger(__name__)
logger.level = logging.INFO


async def async_setup_entry(hass: HomeAssistant,
                            config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    coordinator: PrecosCombustiveisCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    station = coordinator.data

    # Get selected fuel types from config (with fallback for backward compatibility)
    selected_fuel_types = config_entry.data.get(
        CONF_FUEL_TYPES,
        [fuel["TipoCombustivel"] for fuel in station.fuels]
    )

    sensors = [
        PrecosCombustiveisSensor(coordinator, config_entry.data[CONF_STATIONID], fuel["TipoCombustivel"])
        for fuel in station.fuels
        if fuel["TipoCombustivel"] in selected_fuel_types
    ]
    async_add_entities(sensors)


class PrecosCombustiveisSensor(CoordinatorEntity[PrecosCombustiveisCoordinator], SensorEntity):  # type: ignore[misc]
    """Representation of a PrecosCombustiveis Sensor."""

    def __init__(self, coordinator: PrecosCombustiveisCoordinator, station_id: int, fuel_name: str):
        super().__init__(coordinator)
        self._station_id = station_id
        self._fuel_name = fuel_name

        station = coordinator.data
        self._attr_unique_id = f"{DOMAIN}-{self._station_id}-{self._fuel_name}".lower()
        self._attr_name = f"{station.brand} {station.name} {self._fuel_name}"
        self._attr_icon = DEFAULT_ICON
        self._attr_native_unit_of_measurement = UNIT_OF_MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_attribution = ATTRIBUTION
        self._attr_entity_picture = self._get_entity_picture(station)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._station_id))},
            name=station.name,
            model=station.brand,
            manufacturer="DGEG",
        )

        # Set initial dynamic attribute values
        self._update_from_station(station)

    def _get_entity_picture(self, station: Station) -> str | None:
        brand = station.brand
        if brand and brand.lower() != "genérico":
            normalized_brand = unicodedata.normalize("NFD", brand.lower())
            brand_name = "".join(c for c in normalized_brand if c.isalpha())
            return f"/local/precoscombustiveis/{brand_name}.png"
        return None

    def _update_from_station(self, station: Station) -> None:
        """Update dynamic attributes from station data."""
        self._attr_native_value = station.get_price(self._fuel_name)
        self._attr_extra_state_attributes = {
            "GasStationId": self._station_id,
            "Brand": station.brand,
            "Name": station.name,
            "Address": station.address,
            "Latitude": station.latitude,
            "Longitude": station.longitude,
            "StationType": station.type,
            "FuelName": self._fuel_name,
            "LastPriceUpdate": station.get_last_update(self._fuel_name),
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_station(self.coordinator.data)
        self.async_write_ha_state()

