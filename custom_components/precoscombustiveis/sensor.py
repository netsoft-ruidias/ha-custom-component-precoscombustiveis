"""Sensor platform for PrecosCombustiveis integration."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, DEFAULT_ICON, DOMAIN, UNIT_OF_MEASUREMENT
from .coordinator import PrecosCombustiveisCoordinator
from .entity import PrecosCombustiveisEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for all stations in the city entry."""
    coordinators: dict[str, PrecosCombustiveisCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    sensors: list[PrecosCombustiveisSensor] = []

    for station_id, coordinator in coordinators.items():
        station = coordinator.data

        if station is None or not station.fuels:
            _LOGGER.warning("No fuel data for station %s", station_id)
            continue

        for fuel in station.fuels:
            sensors.append(
                PrecosCombustiveisSensor(
                    coordinator=coordinator,
                    station_id=station_id,
                    fuel_type=fuel["TipoCombustivel"],
                )
            )

        _LOGGER.debug(
            "Created %d sensors for station %s (%s)",
            len(station.fuels),
            station_id,
            station.name,
        )

    _LOGGER.info(
        "Created %d total sensors for %d stations in entry %s",
        len(sensors),
        len(coordinators),
        config_entry.title,
    )

    async_add_entities(sensors)


class PrecosCombustiveisSensor(PrecosCombustiveisEntity, SensorEntity):
    """Sensor representing a fuel price at a gas station."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = UNIT_OF_MEASUREMENT
    _attr_icon = DEFAULT_ICON
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: PrecosCombustiveisCoordinator,
        station_id: str,
        fuel_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, station_id)
        self._fuel_type = fuel_type
        self._attr_unique_id = f"{DOMAIN}-{station_id}-{fuel_type}".lower()

    @property
    def name(self) -> str:
        """Return the fuel type as the entity name."""
        return self._fuel_type

    @property
    def native_value(self) -> float | None:
        """Return the current fuel price."""
        station = self.coordinator.data
        if station is None:
            return None

        try:
            return station.getPrice(self._fuel_type)
        except (IndexError, KeyError, ValueError):
            _LOGGER.warning(
                "Could not get price for %s at station %s",
                self._fuel_type,
                self._station_id,
            )
            return None

    @property
    def entity_picture(self) -> str | None:
        """Return the brand logo as the entity picture."""
        station = self.coordinator.data
        if station is None or not station.brand:
            return None

        if station.brand.lower() == "genérico":
            return None

        brand_name = unicodedata.normalize("NFD", station.brand.lower())
        brand_name = "".join(c for c in brand_name if c.isalpha())

        return f"/local/precoscombustiveis/{brand_name}.png"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        station = self.coordinator.data
        if station is None:
            return {}

        return {
            "gas_station_id": self._station_id,
            "brand": station.brand,
            "station_name": station.name,
            "last_price_update": station.getLastUpdate(self._fuel_type),
            "last_fetch_at": self.coordinator.last_fetch_at,
        }
