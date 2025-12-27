# Heating Oil Level Monitor for Home Assistant

A custom Home Assistant integration that tracks your heating oil tank level based on boiler energy consumption. It calculates oil usage from your boiler's kWh readings and provides a visual tank level card.

## Features

- **Automatic Level Calculation**: Uses your boiler's energy consumption (kWh) to calculate oil usage
- **Manual Reading Input**: Calibrate the tank level with actual measurements
- **Visual Tank Card**: Custom Lovelace card showing tank level with color-coded warnings
- **Multiple Sensors**:
  - Oil Level (litres)
  - Oil Level Percentage
  - Oil Consumed Since Last Reading
  - Oil Remaining

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/jtricerolph/homeassistant-heating-oil-level`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Heating Oil Level" and install it
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/heating_oil_level` folder
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Heating Oil Level"
4. Select your boiler energy sensor (must be a sensor with device_class: energy)
5. Enter your tank capacity (default: 1000 litres)
6. Enter the energy conversion rate (default: 10.35 kWh/L)

## Usage

### Initial Setup

After installation, you need to enter your first tank reading:

1. Check your actual oil tank level (via sight glass, dipstick, etc.)
2. Find the "Manual Oil Reading" number entity in Home Assistant
3. Enter your current tank level in litres

The integration will then track consumption based on your boiler's energy usage.

### Adding the Tank Card

1. Go to your Lovelace dashboard
2. Add a new card
3. Search for "Heating Oil Tank Card" or use manual YAML:

```yaml
type: custom:heating-oil-tank-card
title: Oil Tank
entity: sensor.heating_oil_tank_oil_level_percentage
level_entity: sensor.heating_oil_tank_oil_level
reading_entity: number.heating_oil_tank_manual_oil_reading
warning_level: 25
critical_level: 10
show_reading_input: true
```

### Card Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `entity` | Oil level percentage sensor (required) | - |
| `title` | Card title | "Oil Tank" |
| `level_entity` | Oil level sensor in litres | - |
| `reading_entity` | Number entity for manual readings | - |
| `warning_level` | Percentage to show orange warning | 25 |
| `critical_level` | Percentage to show red critical | 10 |
| `show_reading_input` | Show manual reading input field | true |

### Registering the Card Resource

If the card doesn't appear automatically, add it manually:

1. Go to **Settings** > **Dashboards**
2. Click the three dots and select **Resources**
3. Click **Add Resource**
4. Enter URL: `/local/heating-oil-tank-card.js`
5. Select "JavaScript Module"
6. Click "Create"

## How It Works

The integration uses a simple formula to calculate oil consumption:

```
Oil Consumed (L) = Energy Used (kWh) / 10.35 (kWh/L)
```

Where 10.35 kWh/L is the approximate energy content of heating oil (kerosene). You can adjust this value in the integration options if your boiler has different efficiency.

### Calculation Example

- Last reading: 500 litres
- Energy at reading: 10,000 kWh
- Current energy: 10,500 kWh
- Energy used: 500 kWh
- Oil consumed: 500 / 10.35 = 48.3 litres
- Current level: 500 - 48.3 = 451.7 litres

## Entities Created

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.heating_oil_tank_oil_level` | Sensor | Current oil level in litres |
| `sensor.heating_oil_tank_oil_level_percentage` | Sensor | Current level as percentage |
| `sensor.heating_oil_tank_oil_consumed_since_reading` | Sensor | Oil used since last reading |
| `sensor.heating_oil_tank_oil_remaining` | Sensor | Remaining oil in litres |
| `number.heating_oil_tank_manual_oil_reading` | Number | Input for manual readings |

## Tips

- **Regular Calibration**: Update the manual reading periodically (e.g., monthly) to correct any drift
- **After Refill**: Always update the manual reading after receiving an oil delivery
- **Energy Sensor**: Ensure your boiler energy sensor is reporting total consumption in kWh

## Troubleshooting

### Card not showing

1. Check that the card resource is registered
2. Clear browser cache and hard refresh (Ctrl+Shift+R)
3. Check browser console for JavaScript errors

### Incorrect readings

1. Verify your boiler energy sensor is reporting correctly
2. Check the kWh/L conversion rate matches your boiler efficiency
3. Update the manual reading with an actual tank measurement

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
