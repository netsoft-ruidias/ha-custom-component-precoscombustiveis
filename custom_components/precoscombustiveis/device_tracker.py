"""Device tracker platform for PrecosCombustiveis integration."""

from __future__ import annotations

import logging
import unicodedata

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PrecosCombustiveisCoordinator
from .entity import PrecosCombustiveisEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device trackers for all stations in the city entry."""
    coordinators: dict[str, PrecosCombustiveisCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    trackers: list[StationDeviceTracker] = []

    for station_id, coordinator in coordinators.items():
        station = coordinator.data

        if station is None:
            _LOGGER.warning("No data for station %s", station_id)
            continue

        trackers.append(
            StationDeviceTracker(
                coordinator=coordinator,
                station_id=station_id,
            )
        )

        _LOGGER.debug("Created device tracker for station %s (%s)", station_id, station.name)

    _LOGGER.info(
        "Created %d device trackers for entry %s",
        len(trackers),
        config_entry.title,
    )

    async_add_entities(trackers)


class StationDeviceTracker(PrecosCombustiveisEntity, TrackerEntity):
    """Device tracker representing a gas station location."""

    _attr_icon = "mdi:gas-station"
    _attr_name = "Location"

    def __init__(
        self,
        coordinator: PrecosCombustiveisCoordinator,
        station_id: str,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, station_id)
        self._attr_unique_id = f"{DOMAIN}-{station_id}-location"

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        station = self.coordinator.data
        if station is None:
            return None
        try:
            return station.latitude
        except (AttributeError, TypeError):
            return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        station = self.coordinator.data
        if station is None:
            return None
        try:
            return station.longitude
        except (AttributeError, TypeError):
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
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        station = self.coordinator.data
        if station is None:
            return {}

        return {
            "address": station.address,
            "station_type": station.type,
        }
