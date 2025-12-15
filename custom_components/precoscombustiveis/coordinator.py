"""DataUpdateCoordinator for PrecosCombustiveis integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .dgeg import DGEG, Station

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=60)


class PrecosCombustiveisCoordinator(DataUpdateCoordinator[Station]):
    """Coordinator to manage fetching data for a single gas station."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: DGEG,
        station_id: str,
        station_name: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.station_id = station_id
        self.station_name = station_name
        self.last_fetch_at: datetime | None = None

    async def _async_update_data(self) -> Station:
        """Fetch data from DGEG API."""
        try:
            _LOGGER.debug(
                "Fetching data for station %s (%s)",
                self.station_id,
                self.station_name,
            )
            station = await self.api.getStation(self.station_id)

            if station is None:
                raise UpdateFailed(f"Failed to fetch data for station {self.station_id}")

            self.last_fetch_at = dt_util.now()

            _LOGGER.debug(
                "Successfully fetched %d fuel prices for station %s at %s",
                len(station.fuels) if station.fuels else 0,
                self.station_name,
                self.last_fetch_at,
            )
            return station

        except Exception as err:
            raise UpdateFailed(f"Error fetching data for station {self.station_id}: {err}") from err
