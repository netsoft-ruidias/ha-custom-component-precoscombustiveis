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
API_STATIONS_LIST = "https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/PesquisarPostos?qtdPorPagina=99999&pagina=1"
API_URI_TEMPLATE = "https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/GetDadosPosto?id={}"
