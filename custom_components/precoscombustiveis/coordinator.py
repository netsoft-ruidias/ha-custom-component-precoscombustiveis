"""DataUpdateCoordinator for PrecosCombustiveis."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .dgeg import DGEG, Station
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=60)


class PrecosCombustiveisCoordinator(DataUpdateCoordinator[Station]):
    """Coordinator to manage fetching data from DGEG API."""

    def __init__(self, hass: HomeAssistant, api: DGEG, station_id: int) -> None:
        """Initialize the coordinator."""
        self._api = api
        self._station_id = station_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> Station:
        """Fetch data from DGEG API."""
        try:
            station = await self._api.get_station(self._station_id)
            if station is None:
                raise UpdateFailed("No data returned from DGEG API")
            return station
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with DGEG API: {err}") from err
