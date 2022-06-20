"""API to DGEG."""
import aiohttp
import logging

from .const import (
    API_URI_TEMPLATE
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class Station:
    """Represents a STATION card."""

    def __init__(self, id, data):
        self._id = id
        self._data = data
        
    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._data["Nome"]

    @property
    def brand(self):
        return self._data["Marca"]

    @property
    def type(self):
        return self._data["TipoPosto"]

    @property
    def fuels(self):
        return self._data["Combustiveis"]

    @property
    def lastUpdate(self):
        return self._data["DataAtualizacao"]

class DGEG:
    """Interfaces to https://precoscombustiveis.dgeg.gov.pt/"""

    def __init__(self, websession):
        self.websession = websession
        self.json = None

    async def getStation(self, id: str) -> Station:
        """Issue STATION requests."""
        try:
            _LOGGER.debug("Fetching station details...")
            async with self.websession.get(
                API_URI_TEMPLATE.format(id), 
                headers = { 
                    "Content-Type": "application/json" 
                }
            ) as res:
                if res.status == 200 and res.content_type == "application/json":
                    json = await res.json()
                    _LOGGER.debug("Station details", json)
                    return Station(
                        id,
                        json['resultado'])
                raise Exception("Could not retrieve station details from API")
        except aiohttp.ClientError as err:
            _LOGGER.error(err)


