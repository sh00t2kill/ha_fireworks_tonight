# Fireworks Tonight - Home Assistant Custom Component

A Home Assistant custom component that tracks nearby fireworks events using the fireworks-tonight.au API.

## Features

- **Three Sensors:**
  1. **Event Count Sensor**: Shows the number of nearby fireworks events
  2. **Events Details Sensor**: Provides detailed information about each event
  3. **Closest Event Sensor**: Shows location and details of the nearest event
- **Fireworks Calendar**: Automatically creates calendar entries for all nearby events
- **Configurable Distance**: Set maximum distance (in km) to search for events
- **Automatic Location**: Uses Home Assistant's configured latitude/longitude
- **Regular Updates**: Polls for new events every hour

## Installation

### Manual Installation

1. Copy the `custom_components/fireworks_tonight` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to **Configuration** → **Integrations** → **Add Integration**
4. Search for "Fireworks Tonight" and add it

### HACS Installation (if you publish to HACS)

1. Go to HACS → Integrations
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add the repository URL and select "Integration"
5. Install "Fireworks Tonight"

## Configuration

### Via UI

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "Fireworks Tonight"
4. Enter your configuration:
   - **Postcode**: Australian postcode to search around (e.g., "2021")
   - **Max Distance**: Maximum distance in kilometers to search for events (default: 10km)

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `postcode` | Yes | - | Australian postcode (4 digits) |
| `max_distance` | No | 10 | Maximum distance in kilometers |

## Sensors

### Event Count Sensor (`sensor.fireworks_tonight_count`)

Shows the number of nearby fireworks events.

**Attributes:**
- `postcode`: Configured postcode
- `max_distance_km`: Maximum search distance
- `last_updated`: Last update time

### Events Details Sensor (`sensor.fireworks_tonight_events`)

Provides detailed information about all nearby events.

**Attributes:**
- `postcode`: Configured postcode
- `max_distance_km`: Maximum search distance
- `event_count`: Number of events found
- `events`: Array of event details including:
  - `title`: Event name
  - `location`: Event location
  - `coordinates`: Latitude/longitude
  - `distance_km`: Distance from your location
  - `start_time`: Event start time
  - `end_time`: Event end time
  - `description`: Event description
- Individual event attributes: `event_1_title`, `event_1_location`, etc.

### Closest Event Sensor (`sensor.fireworks_tonight_closest_event`)

Shows the location of the nearest fireworks event as its state.

**Attributes:**
- `postcode`: Configured postcode
- `max_distance_km`: Maximum search distance
- `total_events`: Total number of events found
- `title`: Title of the closest event
- `location`: Location of the closest event (same as state)
- `distance_km`: Distance to the closest event
- `coordinates`: Full coordinates object
- `latitude` & `longitude`: Individual coordinate values
- `start_time` & `end_time`: Event timing
- `description`: Event description

## Calendar

### Fireworks Calendar (`calendar.fireworks`)

Automatically creates a calendar called "Fireworks" with entries for all nearby events.

**Features:**
- **Automatic Events**: Creates calendar entries using start_time and end_time from API
- **Rich Descriptions**: Includes event description, distance from home, and coordinates
- **Location Info**: Shows event location in calendar entry
- **Integration**: Works with Home Assistant calendar features and automations

**Event Details:**
- **Title**: Event name from API
- **Time**: Uses start_time and end_time from event data
- **Location**: Event location
- **Description**: Includes original description plus distance and coordinates

## Example Automations

### Notification when events are found

```yaml
automation:
  - alias: "Notify about nearby fireworks"
    trigger:
      - platform: numeric_state
        entity_id: sensor.fireworks_tonight_count
        above: 0
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Fireworks Tonight!"
          message: >
            Found {{ states('sensor.fireworks_tonight_count') }} fireworks event(s) 
            within {{ state_attr('sensor.fireworks_tonight_count', 'max_distance_km') }}km
```

### Display events on dashboard

```yaml
type: entities
entities:
  - entity: sensor.fireworks_tonight_count
  - entity: sensor.fireworks_tonight_events
title: Fireworks Tonight
```

## API Source

This component uses the [fireworks-tonight.au](https://fireworks-tonight.au) API to fetch fireworks event data.

## Troubleshooting

### No events found
- Check that your postcode is valid (4 digits, Australian postcode)
- Increase the `max_distance` if you're in a rural area
- Verify Home Assistant's latitude/longitude are set correctly

### Import errors in development
The import errors you see in the IDE are normal - Home Assistant modules are only available when running within Home Assistant.

## Development

The component is structured as follows:
- `__init__.py`: Main integration setup
- `config_flow.py`: Configuration UI
- `sensor.py`: Sensor entities
- `api.py`: API client for fireworks-tonight.au
- `const.py`: Constants and configuration
- `manifest.json`: Integration metadata

## License

This project is licensed under the MIT License.