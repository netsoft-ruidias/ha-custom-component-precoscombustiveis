# Fuel Price Card

A custom Lovelace card designed specifically for this integration with dynamic color coding.

🔗 **Repository:** [fuel-price-card](https://github.com/fcachado/fuel-price-card)

![Fuel Price Card](../images/card_vertical.png)

## Features

- 🎨 **Dynamic color coding** - Green (cheapest) → Yellow (middle) → Red (most expensive)
- 🖼️ **Automatic brand logos** - Uses `entity_picture` from sensors/device_trackers
- 📱 **Two layouts** - Vertical (compact) or Horizontal (list view)
- 🔧 **Visual editor** - Configure via UI with entity picker, no YAML needed
- ⚡ **Lightweight** - No dependencies on other custom cards

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Frontend**
3. Search for "Fuel Price Card"
4. Click **Download**
5. Reload your browser

### Manual

1. Download `fuel-price-card.js` from the releases
2. Copy to `config/www/community/fuel-price-card/fuel-price-card.js`
3. Add to Lovelace resources:

```yaml
lovelace:
  resources:
    - url: /local/community/fuel-price-card/fuel-price-card.js
      type: module
```

## Configuration

```yaml
type: custom:fuel-price-card
entity: sensor.bp_aveiro_gasoleo_simples
min_entity: sensor.gasoleo_simples_min
max_entity: sensor.gasoleo_simples_max
layout: vertical
```

## Options

| Option       | Type    | Default     | Description                              |
| ------------ | ------- | ----------- | ---------------------------------------- |
| `entity`     | string  | Required    | Fuel price sensor entity                 |
| `name`       | string  | Entity name | Display name (optional override)         |
| `min_entity` | string  | Required    | Sensor with minimum price for comparison |
| `max_entity` | string  | Required    | Sensor with maximum price for comparison |
| `layout`     | string  | `vertical`  | `vertical` or `horizontal`               |
| `show_logo`  | boolean | `true`      | Show brand logo from entity_picture      |
| `show_color` | boolean | `true`      | Show color indication (border/glow)      |

## Layouts

### Vertical Layout

Best for comparing multiple stations side by side.

![Vertical Layout](../images/card_vertical.png)

```yaml
type: horizontal-stack
cards:
  - type: custom:fuel-price-card
    entity: sensor.bp_aveiro_gasoleo_simples
    min_entity: sensor.gasoleo_simples_min
    max_entity: sensor.gasoleo_simples_max
    layout: vertical

  - type: custom:fuel-price-card
    entity: sensor.shell_aguada_gasoleo_simples
    min_entity: sensor.gasoleo_simples_min
    max_entity: sensor.gasoleo_simples_max
    layout: vertical
```

### Horizontal Layout

Best for detailed list view.

![Horizontal Layout](../images/card_horizontal.png)

```yaml
type: vertical-stack
cards:
  - type: custom:fuel-price-card
    entity: sensor.bp_aveiro_gasoleo_simples
    min_entity: sensor.gasoleo_simples_min
    max_entity: sensor.gasoleo_simples_max
    layout: horizontal

  - type: custom:fuel-price-card
    entity: sensor.shell_aguada_gasoleo_simples
    min_entity: sensor.gasoleo_simples_min
    max_entity: sensor.gasoleo_simples_max
    layout: horizontal
```

## Helper Sensors

This card requires min/max helper sensors for color comparison.

📄 **See:** [Helper Sensors Documentation](../helper-sensors.md)

## Color Coding

| Price Position | Color     | Meaning       |
| -------------- | --------- | ------------- |
| Cheapest       | 🟢 Green  | Best price    |
| Middle         | 🟡 Yellow | Average price |
| Most Expensive | 🔴 Red    | Highest price |
