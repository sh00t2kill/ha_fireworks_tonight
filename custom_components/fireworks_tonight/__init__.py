"""The Fireworks Tonight integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .api import FireworksAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "calendar"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fireworks Tonight from a config entry."""
    
    postcode = entry.data["postcode"]
    max_distance = entry.data.get("max_distance", 10)
    
    # Get Home Assistant's latitude and longitude
    latitude = hass.config.latitude
    longitude = hass.config.longitude
    
    api = FireworksAPI(postcode, latitude, longitude, max_distance)
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=api.async_get_all_events,  # Fetch 7 days, filter client-side
        update_interval=timedelta(hours=1),
    )
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok