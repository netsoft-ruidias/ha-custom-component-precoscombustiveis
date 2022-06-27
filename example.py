import asyncio
import aiohttp

from custom_components.precoscombustiveis.dgeg import DGEG, Station

async def main():
    async with aiohttp.ClientSession() as session:
        api = DGEG(session)

        print("")
        print("Please type the service station ID from which you want to obtain the prices.")
        print("Go to https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/ListarDadosPostos,")
        print("search for the desired station and copy the `Id`.")
        stationId = input("Enter the Gas Station Id..: ")

        station = await api.getStation(stationId)
        if (station):
            print ("Station Id......:", station.id)
            print ("Station Name....:", station.name)
            print ("Station Brand...:", station.brand)
            print ("Station Address.:", station.address)
            print ("Station Type....:", station.type)

asyncio.get_event_loop().run_until_complete(main())