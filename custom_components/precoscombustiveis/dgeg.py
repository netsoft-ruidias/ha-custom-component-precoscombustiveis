"""API to DGEG."""

import logging
from typing import Dict
from datetime import datetime
import aiohttp

from .const import (
    API_URI_TEMPLATE,
    API_STATIONS_LIST,
    DISTRITOS
)

logger = logging.getLogger(__name__)

class Station:
    """Represents a STATION card."""

    def __init__(self, id, data):
        self._id = id
        self._data = data
        
    @property
    def id(self):
        """Return the station ID."""
        return self._id

    @property
    def name(self):
        """Return the station NAME."""
        return self._data["Nome"]

    @property
    def brand(self):
        """Return the station BRAND."""
        return self._data["Marca"]

    @property
    def type(self):
        """Return the station TYPE."""
        return self._data["TipoPosto"]

    @property
    def address(self):
        """Return the station ADDRESS."""
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
        """Return the station LATITUDE."""
        return float(self._data["Morada"]["Latitude"])
    
    @property
    def longitude(self) -> float:
        """Return the station LONGITUDE."""
        return float(self._data["Morada"]["Longitude"])

    @property
    def fuels(self):
        """Return the station FUELS."""
        return self._data["Combustiveis"]

    def getLastUpdate(self, fuelType) -> datetime | None:
        """Return the station LAST UPDATE for a given fuel type."""
        fuel = [f for f in self._data["Combustiveis"] if f["TipoCombustivel"] == fuelType][0]
        if (fuel):
            return datetime.strptime(
                fuel["DataAtualizacao"],
                '%Y-%m-%d %H:%M')
        return None

    def getPrice(self, fuelType) -> float:
        """Return the station PRICE for a given fuel type."""
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

    async def list_stations(self, distrito_id: str) -> list[Dict]:
        """Get list of all stations."""
        try:
            logger.debug(f"Fetching stations list for distrito Id:{distrito_id} ({DISTRITOS[distrito_id]})...")
            async with self.websession.get(
                API_STATIONS_LIST.format(distrito_id), 
                headers={ 
                    "Content-Type": "application/json" 
                },
                ssl=False  # Disable SSL verification
            ) as res:
                if res.status == 200:
                    json = await res.json()
                    # Sort stations by name for better display (handle None values defensively)
                    def _safe_lower(value):
                        return value.lower() if isinstance(value, str) else ""

                    return sorted(
                        json.get('resultado') or [],
                        key=lambda x: (
                            _safe_lower(x.get('Localidade')),
                            _safe_lower(x.get('Marca')),
                            _safe_lower(x.get('Nome'))
                        )
                    )
                else:
                    logger.error("Failed to fetch stations list. Status: %s", res.status)
                    return []
        except Exception as ex:
            logger.error("Error fetching stations list: %s", str(ex))
            return []

    async def getStation(self, id: str) -> Station:
        """Issue GAS STATION requests."""
        try:
            logger.debug(f"Fetching details for gas station Id:{id}...")
            async with self.websession.get(
                API_URI_TEMPLATE.format(id), 
                headers={ 
                    "Content-Type": "application/json" 
                },
                ssl=False  # Disable SSL verification
            ) as res:
                if res.status == 200 and res.content_type == "application/json":
                    json = await res.json()
                    return Station(
                        id,
                        json['resultado'])
                raise Exception("Could not retrieve gas station details from API")
        except aiohttp.ClientError as err:
            logger.error(err)
            raise err

    async def testStation(self, id: str) -> str:
        """Test if gas stationId exists."""
        station = await self.getStation(id)
        if (not (not station.name and not station.fuels)):
            return station.name
        else:
            return ""
        
