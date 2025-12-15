"""Base entity for PrecosCombustiveis integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PrecosCombustiveisCoordinator


class PrecosCombustiveisEntity(CoordinatorEntity[PrecosCombustiveisCoordinator]):
    """Base entity for PrecosCombustiveis."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrecosCombustiveisCoordinator,
        station_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._station_id = station_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        station = self.coordinator.data
        if station is None:
            return DeviceInfo(
                identifiers={(DOMAIN, self._station_id)},
                name=f"Gas Station {self._station_id}",
                manufacturer="DGEG",
                entry_type=DeviceEntryType.SERVICE,
            )

        # Avoid duplication if station name already starts with brand
        if (
            station.name
            and station.brand
            and station.name.lower().startswith(station.brand.lower())
        ):
            device_name = station.name
        else:
            device_name = f"{station.brand} - {station.name}"

        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=device_name,
            manufacturer=station.brand,
            model=station.type,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://precoscombustiveis.dgeg.gov.pt/",
        )
