"""Simple test file to demonstrate the DGEG API usage."""

import asyncio
import aiohttp

from custom_components.precoscombustiveis.dgeg import DGEG, Station

async def main():
    """Simple test function to demonstrate the DGEG API usage."""
    async with aiohttp.ClientSession() as session:
        api = DGEG(session)

        print("")
        print("Please type the service station ID from which you want to obtain the prices.")
        print("Go to https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/ListarDadosPostos,")
        print("search for the desired station and copy the `Id`.")
        station_id = input("Enter the Gas Station Id..: ") or "65167"

        station: Station = await api.get_station(int(station_id))
        if (station):
            print ("Station Id.......:", station.id)
            print ("Station Name.....:", station.name)
            print ("Station Brand....:", station.brand)
            print ("Station Address..:", station.address)
            print ("GPS..............:", station.latitude, station.longitude)
            print ("Station Type.....:", station.type)
            print (station.fuels)
            print ("Gasóleo simples..:", station.getPrice("Gasóleo simples"), "€", "(", station.getLastUpdate("Gasóleo simples"), ")")
            print ("Gasóleo especial.:", station.getPrice("Gasóleo especial"), "€", "(", station.getLastUpdate("Gasóleo especial"), ")")
        else:
            print ("Gas Station not found!")


asyncio.get_event_loop().run_until_complete(main())
