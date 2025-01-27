DOMAIN = "precoscombustiveis"
PLATFORM = "sensor"
DOMAIN_DATA = f"{DOMAIN}_data"

ATTRIBUTION = "Data provided by https://precoscombustiveis.dgeg.gov.pt/"

DEFAULT_ICON = "mdi:gas-station"
UNIT_OF_MEASUREMENT = "€"

CONF_STATIONID = "stationId"

CONF_STATION_NAME = "station_name"
CONF_STATION_BRAND = "station_brand"
CONF_STATION_ADDRESS = "station_address"

# API endpoints 
API_STATIONS_LIST = "https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/PesquisarPostos?idDistrito={}&qtdPorPagina=99999&pagina=1"
API_URI_TEMPLATE = "https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/GetDadosPosto?id={}"

DISTRITOS = {
    1: "Aveiro",
    2: "Beja",
    3: "Braga", 
    4: "Bragança",
    5: "Castelo Branco",
    6: "Coimbra",
    7: "Évora",
    8: "Faro",
    9: "Guarda",
    10: "Leiria", 
    11: "Lisboa",
    12: "Portalegre",
    13: "Porto",
    14: "Santarém",
    15: "Setúbal",
    16: "Viana do Castelo",
    17: "Vila Real",
    18: "Viseu"
}