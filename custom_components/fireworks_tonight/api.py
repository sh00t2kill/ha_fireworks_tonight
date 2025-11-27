"""API client for Fireworks Tonight."""
import asyncio
import logging
import math
from typing import Any, Dict, List

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class FireworksAPI:
    """API client for Fireworks Tonight service."""
    
    def __init__(self, postcode: str, latitude: float, longitude: float, max_distance: float = 10):
        """Initialize the API client."""
        self.postcode = postcode
        self.latitude = latitude
        self.longitude = longitude
        self.max_distance = max_distance
        self.base_url = "https://fireworks-tonight.au/api/v1/"
        self._session = None
    
    async def _get_session(self):
        """Get aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def async_close(self):
        """Close aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on earth (in km)."""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    async def _get_locations(self, postcode_prefix: str) -> str | None:
        """Get locations by postcode prefix."""
        session = await self._get_session()
        url = f"{self.base_url}locations?startswith={postcode_prefix}"
        
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data[0] if data else None
        except Exception as err:
            _LOGGER.error("Error getting locations: %s", err)
            return None
    
    async def _get_location_id(self, postcode: str) -> int | None:
        """Get location ID for a postcode."""
        location = await self._get_locations(postcode)
        if not location:
            return None
        
        parts = location.split(',')
        session = await self._get_session()
        url = f"{self.base_url}locations?locality={parts[0].strip().lower()}&postcode={parts[1].strip()}"
        
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data[0]['id'] if data else None
        except Exception as err:
            _LOGGER.error("Error getting location ID: %s", err)
            return None
    
    async def _get_events(self, location_id: int, days: int = 1) -> List[Dict[str, Any]]:
        """Get events for a location."""
        session = await self._get_session()
        url = f"{self.base_url}events?location={location_id}&days={days}"
        
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data
        except Exception as err:
            _LOGGER.error("Error getting events: %s", err)
            return []
    
    async def async_get_events(self) -> Dict[str, Any]:
        """Get nearby fireworks events for today only (for sensors)."""
        return await self._get_events_for_days(1)
    
    async def async_get_all_events(self) -> Dict[str, Any]:
        """Get nearby fireworks events for 7 days (for calendar)."""
        return await self._get_events_for_days(7)
    
    async def _get_events_for_days(self, days: int) -> Dict[str, Any]:
        """Get nearby fireworks events for specified number of days."""
        try:
            location_id = await self._get_location_id(self.postcode)
            if not location_id:
                _LOGGER.warning("Could not find location for postcode: %s", self.postcode)
                return {"event_count": 0, "events": []}
            
            events = await self._get_events(location_id, days=days)
            nearby_events = []
            
            for event in events:
                location = event.get('location', {})
                coordinates = location.get('coordinates', {})
                event_lat = coordinates.get('latitude')
                event_lon = coordinates.get('longitude')
                
                if event_lat is None or event_lon is None:
                    continue
                
                # Calculate distance
                distance = self.calculate_distance(
                    self.latitude, self.longitude, event_lat, event_lon
                )
                
                if distance <= self.max_distance:
                    nearby_event = {
                        "title": event.get('name', 'Unknown Event'),  # API uses 'name' not 'title'
                        "location": event.get('rawlocation', 'Unknown Location'),
                        "locality": location.get('locality', 'Unknown'),  # Add locality from location object
                        "coordinates": {
                            "latitude": event_lat,
                            "longitude": event_lon
                        },
                        "distance_km": round(distance, 2),
                        "date": event.get('date'),          # Separate date field
                        "start_time": event.get('start_time'),  # Correct field name
                        "end_time": event.get('end_time'),      # Correct field name
                        "description": event.get('description', ''),
                        "source": event.get('source', ''),
                        "event_id": event.get('id')
                    }
                    nearby_events.append(nearby_event)
            
            return {
                "event_count": len(nearby_events),
                "events": nearby_events
            }
            
        except Exception as err:
            _LOGGER.error("Error fetching events: %s", err)
            return {"event_count": 0, "events": []}