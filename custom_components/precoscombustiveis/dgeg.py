"""API to DGEG."""
from typing import Dict, Optional
from datetime import datetime
from aiohttp import ClientSession
import logging

from datetime import datetime

from .const import (
    API_URI_TEMPLATE,
    API_STATIONS_LIST
)

_LOGGER = logging.getLogger(__name__)

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
    def address(self):
        if self._data["Morada"]:
            return [
                self._data["Morada"]["Morada"],
                self._data["Morada"]["Localidade"],
                self._data["Morada"]["CodPostal"]
            ]
        else:
            return None

    @property
    def latitude(self) -> float:
        return float(self._data["Morada"]["Latitude"])
    
    @property
    def longitude(self) -> float:
        return float(self._data["Morada"]["Longitude"])

    @property
    def fuels(self):
        return self._data["Combustiveis"]

    def getLastUpdate(self, fuelType) -> datetime:
        fuel = [f for f in self._data["Combustiveis"] if f["TipoCombustivel"] == fuelType][0]
        if (fuel):
            return datetime.strptime(
                fuel["DataAtualizacao"],
                '%Y-%m-%d %H:%M')
        return None

    def getPrice(self, fuelType) -> float:
        fuel = [f for f in self._data["Combustiveis"] if f["TipoCombustivel"] == fuelType][0]
        if (fuel):               
            return float(fuel["Preco"]
                .replace(" €/litro", "")
                .replace(",", "."))
        else:
            return 0

class DGEG:
    """Interfaces to https://precoscombustiveis.dgeg.gov.pt/"""

    def __init__(self, websession):
        self.websession = websession

    async def list_stations(self) -> list[Dict]:
        """Get list of all stations."""
        try:
            async with self.websession.get(API_STATIONS_LIST) as res:
                if res.status == 200:
                    json = await res.json()
                    # Sort stations by name for better display
                    return sorted(
                        json['resultado'],
                        key=lambda x: (
                            x.get('Distrito', '').lower(),
                            x.get('Localidade', '').lower(),
                            x.get('Marca', '').lower(), 
                            x.get('Nome', '').lower()
                        )
                    )
                else:
                    _LOGGER.error("Failed to fetch stations list. Status: %s", res.status)
                    return []
        except Exception as ex:
            _LOGGER.error("Error fetching stations list: %s", str(ex))
            return []

    async def getStation(self, id: str) -> Station:
        """Issue GAS STATION requests."""
        try:
            _LOGGER.debug(f"Fetching details for gas station Id:{id}...")
            async with self.websession.get(
                API_URI_TEMPLATE.format(id), 
                headers={ 
                    "Content-Type": "application/json" 
                }
            ) as res:
                if res.status == 200 and res.content_type == "application/json":
                    json = await res.json()
                    return Station(
                        id,
                        json['resultado'])
                raise Exception("Could not retrieve gas station details from API")
        except aiohttp.ClientError as err:
            _LOGGER.error(err)

    async def testStation(self, id: str) -> str:
        """Test if gas stationId exists."""
        station = await self.getStation(id)
        if (not (not station.name and not station.fuels)):
            return station.name
        else:
            return None
        #return not (not station.name and not station.fuels)
