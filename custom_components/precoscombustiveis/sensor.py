"""Platform for sensor integration."""
from __future__ import annotations

import logging
import unicodedata


from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_ICON,
    DOMAIN,
    UNIT_OF_MEASUREMENT,
    ATTRIBUTION,
    CONF_ENTRY_TYPE,
    CONF_FORECAST_FUELS,
    CONF_STATIONID,
    CONF_FUEL_TYPES,
    ENTRY_TYPE_FORECAST,
    ENTRY_TYPE_STATION,
    FORECAST_ATTRIBUTION,
    FORECAST_FUELS,
    FORECAST_UNIQUE_ID)
from .coordinator import ForecastCoordinator, PrecosCombustiveisCoordinator
from .dgeg import Station
from .forecast import FuelForecast, TREND_DOWN, TREND_NEUTRAL, TREND_UP

logger = logging.getLogger(__name__)
logger.level = logging.INFO

FORECAST_ICONS = {
    TREND_UP: "mdi:trending-up",
    TREND_DOWN: "mdi:trending-down",
    TREND_NEUTRAL: "mdi:trending-neutral",
}


async def async_setup_entry(hass: HomeAssistant,
                            config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback):
    """Setup sensor platform."""
    # Entries created before the forecast existed have no entry type: they are stations
    if config_entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_STATION) == ENTRY_TYPE_FORECAST:
        _setup_forecast_sensors(hass, config_entry, async_add_entities)
        return

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


def _setup_forecast_sensors(hass: HomeAssistant,
                            config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Create the selected forecast sensors and delete the ones no longer selected."""
    coordinator: ForecastCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = [
        ForecastSensor(coordinator, fuel)
        for fuel in config_entry.data.get(CONF_FORECAST_FUELS, [])
        if fuel in FORECAST_FUELS
    ]
    wanted = {sensor.unique_id for sensor in sensors}

    entity_registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        if entity.unique_id not in wanted:
            entity_registry.async_remove(entity.entity_id)

    if not wanted:
        device_registry = dr.async_get(hass)
        for device in dr.async_entries_for_config_entry(device_registry, config_entry.entry_id):
            device_registry.async_remove_device(device.id)

    async_add_entities(sensors)


class ForecastSensor(CoordinatorEntity[ForecastCoordinator], SensorEntity):  # type: ignore[misc]
    """Weekly price variation forecast for a fuel, in €/L (negative = fall)."""

    _attr_native_unit_of_measurement = UNIT_OF_MEASUREMENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = FORECAST_ATTRIBUTION

    def __init__(self, coordinator: ForecastCoordinator, fuel: str):
        super().__init__(coordinator)
        self._fuel = fuel
        self._attr_unique_id = f"{DOMAIN}-forecast-{fuel}"
        self._attr_name = f"Previsão semanal {FORECAST_FUELS[fuel]}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, FORECAST_UNIQUE_ID)},
            name="Previsão semanal",
            manufacturer="precocombustiveis.pt",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _forecast(self) -> FuelForecast | None:
        return self.coordinator.data.get(self._fuel) if self.coordinator.data else None

    @property
    def available(self) -> bool:
        """The sensor is unavailable if the page has no forecast for this fuel."""
        return super().available and self._forecast is not None

    @property
    def native_value(self) -> float | None:
        forecast = self._forecast
        return forecast.variation if forecast else None

    @property
    def icon(self) -> str:
        forecast = self._forecast
        return FORECAST_ICONS[forecast.trend if forecast else TREND_NEUTRAL]

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        forecast = self._forecast
        if forecast is None:
            return None
        return {
            "ForecastStart": forecast.start,
            "ForecastEnd": forecast.end,
            "LastUpdate": forecast.last_update,
            "Trend": forecast.trend,
            "VariationLevel": forecast.level,
            "FormattedVariation": forecast.formatted,
        }

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

