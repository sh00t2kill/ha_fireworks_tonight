"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        FireworksCountSensor(coordinator, config_entry),
        FireworksEventsSensor(coordinator, config_entry),
        FireworksClosestEventSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)

class FireworksCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the number of nearby fireworks events."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_count"
        self._attr_name = f"Fireworks Tonight Count"
        self._attr_icon = "mdi:firework"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    def _get_todays_events(self) -> list:
        """Filter events to only include today's events."""
        if not self.coordinator.data:
            return []
        
        from datetime import date
        today = date.today().isoformat()  # Format: "2025-11-25"
        
        all_events = self.coordinator.data.get("events", [])
        todays_events = [event for event in all_events if event.get("date") == today]
        return todays_events
    
    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return len(self._get_todays_events())
    
    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "events"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        
        postcode = self.config_entry.data.get("postcode", "Unknown")
        max_distance = self.config_entry.data.get("max_distance", 10)
        
        return {
            "postcode": postcode,
            "max_distance_km": max_distance,
            "last_updated": datetime.now().isoformat(),
        }

class FireworksEventsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for fireworks events details."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_events"
        self._attr_name = f"Fireworks Tonight Events"
        self._attr_icon = "mdi:firework"
    
    def _get_todays_events(self) -> list:
        """Filter events to only include today's events."""
        if not self.coordinator.data:
            return []
        
        from datetime import date
        today = date.today().isoformat()  # Format: "2025-11-25"
        
        all_events = self.coordinator.data.get("events", [])
        todays_events = [event for event in all_events if event.get("date") == today]
        return todays_events
    
    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        events = self._get_todays_events()
        event_count = len(events)
        if event_count == 0:
            return "No events"
        elif event_count == 1:
            return "1 event"
        else:
            return f"{event_count} events"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes with event details."""
        events = self._get_todays_events()
        postcode = self.config_entry.data.get("postcode", "Unknown")
        max_distance = self.config_entry.data.get("max_distance", 10)
        
        attributes = {
            "postcode": postcode,
            "max_distance_km": max_distance,
            "event_count": len(events),
            "events": events,
            "last_updated": datetime.now().isoformat(),
        }
        
        # Add individual event details as separate attributes for easy access
        for i, event in enumerate(events):
            attributes[f"event_{i+1}_title"] = event.get("title", "Unknown")
            attributes[f"event_{i+1}_location"] = event.get("location", "Unknown")
            attributes[f"event_{i+1}_distance_km"] = event.get("distance_km", 0)
            attributes[f"event_{i+1}_start_time"] = event.get("start_time", "Unknown")
            
        return attributes

class FireworksClosestEventSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the closest fireworks event."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_closest_event"
        self._attr_name = f"Fireworks Tonight Closest Event"
        self._attr_icon = "mdi:map-marker-distance"
    
    def _get_todays_events(self) -> list:
        """Filter events to only include today's events."""
        if not self.coordinator.data:
            return []
        
        from datetime import date
        today = date.today().isoformat()  # Format: "2025-11-25"
        
        all_events = self.coordinator.data.get("events", [])
        todays_events = [event for event in all_events if event.get("date") == today]
        return todays_events
    
    @property
    def native_value(self) -> str:
        """Return the location of the closest event."""
        events = self._get_todays_events()
        if not events:
            return "No events"
        
        # Sort events by distance and get the closest one
        closest_event = min(events, key=lambda x: x.get("distance_km", float('inf')))
        return closest_event.get("location", "Unknown Location")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes with closest event details."""
        events = self._get_todays_events()
        postcode = self.config_entry.data.get("postcode", "Unknown")
        max_distance = self.config_entry.data.get("max_distance", 10)
        
        base_attributes = {
            "postcode": postcode,
            "max_distance_km": max_distance,
            "total_events": len(events),
            "last_updated": datetime.now().isoformat(),
        }
        
        if not events:
            return base_attributes
        
        # Find the closest event
        closest_event = min(events, key=lambda x: x.get("distance_km", float('inf')))
        
        # Add all details of the closest event as attributes
        base_attributes.update({
            "title": closest_event.get("title", "Unknown Event"),
            "location": closest_event.get("location", "Unknown Location"),
            "distance_km": closest_event.get("distance_km", 0),
            "coordinates": closest_event.get("coordinates", {}),
            "latitude": closest_event.get("coordinates", {}).get("latitude"),
            "longitude": closest_event.get("coordinates", {}).get("longitude"),
            "start_time": closest_event.get("start_time", "Unknown"),
            "end_time": closest_event.get("end_time", "Unknown"),
            "description": closest_event.get("description", ""),
        })
        
        return base_attributes