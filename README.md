![GitHub](https://img.shields.io/github/license/netsoft-ruidias/ha-custom-component-precoscombustiveis?style=for-the-badge)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/netsoft-ruidias/ha-custom-component-precoscombustiveis?style=for-the-badge)
![GitHub Release Date](https://img.shields.io/github/release-date/netsoft-ruidias/ha-custom-component-precoscombustiveis?style=for-the-badge)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/netsoft-ruidias/ha-custom-component-precoscombustiveis?style=for-the-badge)

# Preços dos Combustíveis - DGEG
Fuel Prices in Portugal - Custom Component for Home Assistant

The data source for this integration is the [DGEG - Direcção-Geral de Energia e Geologia](https://www.dgeg.gov.pt/).

The author of this project categorically rejects any and all responsibility for the fuels prices that were presented by the integration.

# Installation
## HACS (Recommended)
This integration can be added to HACS as a custom (non-default) repository.

Assuming you have already installed and configured HACS, follow these steps:

1. Navigate to the HACS integrations page at http://<your-home-assistant>:8123/hacs/integrations.
2. Click the 3 vertical dots menu in the top right corner.
3. Choose 'Custom repositories'
4. Enter the name of this repository (https://github.com/netsoft-ruidias/ha-custom-component-precoscombustiveis/) in the text field in the dialog.
5. Choose 'Integration' from the Category list in the dialog.
6. Click 'Add'. The repository will now be added to your HACS.
7. Click the 'x' to close the dialog.
8. The integration is now visible. Click 'Install', and click 'Install' again.
9. Ready! Now continue with the configuration.

## Manual
Manual installation is not recomended

# Configuration

## Through the interface
1. Navigate to `Settings > Devices & Services` and then click `Add Integration`
2. Search for `Precos Combustiveis DGEG.PT integration`
3. (Go to [dgeg](https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/ListarDadosPostos), search for the desired gas station and copy it's `Id`)
4. Enter the StationId you copied in the previous step
5. Repeat the procedure as many times as desired to include other stations

## Through configuration.yaml
Manual configuration through _configuration.yaml_ is not recomended, please use the interface configuration as described above

## Sample
One can use the standard [entities](https://www.home-assistant.io/dashboards/entities/) card to display data in the UI:

```yaml
type: entities
entities:
  - entity: sensor.galp_irmaos_peres_lda_souto_gasoleo_simples_2
    name: Gasóleo simples
  - entity: sensor.galp_irmaos_peres_lda_souto_gasoleo_especial
    name: Gasóleo especial
  - entity: sensor.galp_irmaos_peres_lda_souto_gasoleo_colorido
    name: Gasóleo colorido
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_especial_95
    name: Gasolina especial 95
  - entity: sensor.galp_irmaos_peres_lda_souto_gasoleo_simples
    name: Gasolina especial 98
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_simples_95
    name: Gasolina simples 95
  - type: divider
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_simples_95
    type: attribute
    attribute: Name
    name: Empresa
    icon: mdi:greenhouse
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_simples_95
    type: attribute
    attribute: Brand
    name: Marca
    icon: mdi:widgets
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_simples_95
    type: attribute
    attribute: stationType
    name: Tipo de Posto
  - entity: sensor.galp_irmaos_peres_lda_souto_gasolina_simples_95
    type: attribute
    attribute: lastPriceUpdate
    name: Ultima Actualização de Preço
    icon: mdi:reload
title: GALP Irmãos Peres, Lda
```
Which will result in the following card:

![Sample Card](https://github.com/netsoft-ruidias/ha-custom-component-precoscombustiveis/blob/main/docs/samplecard.png?raw=true)

Or, if you prefer, you can even use a [custom:auto-entities](https://github.com/thomasloven/lovelace-auto-entities) card to auto display your prices:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Diesel Prices
filter:
  include:
    - entity_id: /sensor\..*_gasoleo/
sort:
  method: state
  numeric: true
  reverse: false
```


# Legal notice
This is a personal project and isn't in any way affiliated with, sponsored or endorsed by [DGEG](https://www.dgeg.gov.pt/).

All product names, trademarks and registered trademarks in (the images in) this repository, are property of their respective owners. All images in this repository are used by the project for identification purposes only.