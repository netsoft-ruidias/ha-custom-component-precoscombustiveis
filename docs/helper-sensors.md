# Helper Sensors (Required)

These template sensors are **required** for the dynamic color cards to work. They calculate the minimum and maximum prices across all your configured gas stations.

## Configuration

Add to your `configuration.yaml`:

```yaml
template: !include templates.yaml
```

Then create `templates.yaml` with:

```yaml
- sensor:
    - name: "Gasóleo Simples Min"
      unique_id: gasoleo_simples_min
      unit_of_measurement: "€"
      state: >
        {% set sensors = [
          states('sensor.your_station_1_gasoleo_simples'),
          states('sensor.your_station_2_gasoleo_simples'),
          states('sensor.your_station_3_gasoleo_simples')
        ] | reject('eq', 'unknown') | reject('eq', 'unavailable') | map('float') | list %}
        {{ sensors | min if sensors else 0 }}

    - name: "Gasóleo Simples Max"
      unique_id: gasoleo_simples_max
      unit_of_measurement: "€"
      state: >
        {% set sensors = [
          states('sensor.your_station_1_gasoleo_simples'),
          states('sensor.your_station_2_gasoleo_simples'),
          states('sensor.your_station_3_gasoleo_simples')
        ] | reject('eq', 'unknown') | reject('eq', 'unavailable') | map('float') | list %}
        {{ sensors | max if sensors else 0 }}

    - name: "Gasolina 95 Min"
      unique_id: gasolina_95_min
      unit_of_measurement: "€"
      state: >
        {% set sensors = [
          states('sensor.your_station_1_gasolina_simples_95'),
          states('sensor.your_station_2_gasolina_simples_95'),
          states('sensor.your_station_3_gasolina_simples_95')
        ] | reject('eq', 'unknown') | reject('eq', 'unavailable') | map('float') | list %}
        {{ sensors | min if sensors else 0 }}

    - name: "Gasolina 95 Max"
      unique_id: gasolina_95_max
      unit_of_measurement: "€"
      state: >
        {% set sensors = [
          states('sensor.your_station_1_gasolina_simples_95'),
          states('sensor.your_station_2_gasolina_simples_95'),
          states('sensor.your_station_3_gasolina_simples_95')
        ] | reject('eq', 'unknown') | reject('eq', 'unavailable') | map('float') | list %}
        {{ sensors | max if sensors else 0 }}
```

## Usage

Replace `sensor.your_station_X_*` with your actual sensor entity IDs.

These sensors are used by the [Fuel Price Card](cards/fuel-price-card.md) to calculate the color gradient.

## Created Entities

| Entity | Description |
|--------|-------------|
| `sensor.gasoleo_simples_min` | Lowest diesel price |
| `sensor.gasoleo_simples_max` | Highest diesel price |
| `sensor.gasolina_95_min` | Lowest petrol 95 price |
| `sensor.gasolina_95_max` | Highest petrol 95 price |

