"""Platform for calendar integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        FireworksCalendar(coordinator, config_entry),
    ]
    
    async_add_entities(entities)

class FireworksCalendar(CoordinatorEntity, CalendarEntity):
    """A calendar entity for fireworks events."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_calendar"
        self._attr_name = "Fireworks"
        self._attr_icon = "mdi:firework"
    
    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        events = self._get_calendar_events()
        if not events:
            return None
        
        # Find the next event that hasn't ended yet
        now = dt_util.utcnow()
        upcoming_events = [
            event for event in events 
            if event.end_datetime_local > now
        ]
        
        if not upcoming_events:
            return None
        
        # Sort by start time and return the earliest
        upcoming_events.sort(key=lambda x: x.start_datetime_local)
        return upcoming_events[0]
    
    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events = self._get_calendar_events()
        
        # Filter events within the requested date range
        filtered_events = []
        for event in events:
            # Check if event overlaps with the requested range
            if (event.start_datetime_local < end_date and 
                event.end_datetime_local > start_date):
                filtered_events.append(event)
        
        return filtered_events
    
    def _get_calendar_events(self) -> list[CalendarEvent]:
        """Convert fireworks events to calendar events."""
        # Use all 7 days of events for calendar
        if not self.coordinator.data:
            return []
        
        events = self.coordinator.data.get("events", [])
        calendar_events = []
        
        for event in events:
            date_str = event.get("date")
            start_time_str = event.get("start_time")
            end_time_str = event.get("end_time")
            
            if not date_str or not start_time_str or not end_time_str:
                continue
            
            try:
                # Parse the date and times separately, then combine them
                start_time = self._parse_datetime_from_parts(date_str, start_time_str)
                end_time = self._parse_datetime_from_parts(date_str, end_time_str)
                
                if not start_time or not end_time:
                    continue
                
                # Create calendar event
                calendar_event = CalendarEvent(
                    start=start_time,
                    end=end_time,
                    summary=event.get("location", "Fireworks Event"),  # Use location as title instead of name
                    description=self._build_event_description(event),
                    location=event.get("location", ""),
                    uid=f"fireworks_{event.get('event_id', hash(str(event)))}",  # Use API ID if available
                )
                
                calendar_events.append(calendar_event)
                
            except Exception as err:
                _LOGGER.warning(
                    "Failed to parse event times for %s: %s", 
                    event.get("title", "Unknown"), 
                    err
                )
                continue
        
        return calendar_events
    
    def _parse_datetime_from_parts(self, date_str: str, time_str: str) -> datetime | None:
        """Parse datetime from separate date and time strings."""
        if not date_str or not time_str:
            return None
        
        try:
            # API format: date="2025-11-25", time="20:15"
            # Combine them into a single datetime string
            combined_str = f"{date_str} {time_str}"
            
            # Try different combined formats
            formats_to_try = [
                "%Y-%m-%d %H:%M",           # ISO date with HH:MM time
                "%Y-%m-%d %H:%M:%S",        # ISO date with HH:MM:SS time
                "%d-%m-%Y %H:%M",           # DD-MM-YYYY with HH:MM time
                "%d/%m/%Y %H:%M",           # DD/MM/YYYY with HH:MM time
            ]
            
            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(combined_str, fmt)
                    # Assume local timezone since API doesn't specify
                    dt = dt_util.as_local(dt)
                    return dt
                except ValueError:
                    continue
            
            _LOGGER.warning("Could not parse date/time: %s %s", date_str, time_str)
            return None
            
        except Exception as err:
            _LOGGER.warning("Error parsing date/time %s %s: %s", date_str, time_str, err)
            return None
    
    def _build_event_description(self, event: dict[str, Any]) -> str:
        """Build a description for the calendar event."""
        description_parts = []
        
        if event.get("description"):
            description_parts.append(event["description"])
        
        # Add distance information
        distance = event.get("distance_km")
        if distance is not None:
            description_parts.append(f"Distance: {distance:.1f} km from home")
        
        # Add coordinates
        coords = event.get("coordinates", {})
        if coords.get("latitude") and coords.get("longitude"):
            lat = coords["latitude"]
            lon = coords["longitude"]
            description_parts.append(f"Coordinates: {lat}, {lon}")
        
        return "\n\n".join(description_parts)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        events = self.coordinator.data.get("events", [])
        postcode = self.config_entry.data.get("postcode", "Unknown")
        
        return {
            "postcode": postcode,
            "total_events": len(events),
            "last_updated": self.coordinator.last_update_success,
        }