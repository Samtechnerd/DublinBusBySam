"""Sensor platform for Dublin Bus by Sam."""
from __future__ import annotations
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_STOP_ID

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    stop_id = entry.data[CONF_STOP_ID]
    
    async_add_entities([DublinBusSensor(coordinator, stop_id)])

class DublinBusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Dublin Bus Sensor."""

    def __init__(self, coordinator, stop_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._attr_name = f"Dublin Bus {stop_id}"
        self._attr_unique_id = f"dublin_bus_{stop_id}"
        self._attr_icon = "mdi:bus-clock"
        self._attr_unit_of_measurement = "min"

    def _get_valid_trips(self):
        """Filter out buses that have already passed."""
        trips = self.coordinator.data.get("upcomingTrips", [])
        valid_trips = []
        
        now = dt_util.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_seconds = (now - midnight).total_seconds()

        for trip in trips:
            departure_timestamp = trip.get("departureTimestamp")
            if departure_timestamp is None:
                continue

            # Calculate raw difference in minutes
            diff_seconds = departure_timestamp - current_seconds
            minutes = int(diff_seconds / 60)

            # Only keep buses that are in the future or just left (>-2 mins)
            if minutes >= -1:
                # Add the calculated minutes to the trip object temporarily for easy access
                trip["calc_minutes"] = max(0, minutes)
                valid_trips.append(trip)
                
        return valid_trips

    @property
    def native_value(self):
        """Return minutes until the NEXT valid bus."""
        valid_trips = self._get_valid_trips()
        
        if not valid_trips:
            return 0 # No valid upcoming buses

        # The first item in our filtered list is the next bus
        return valid_trips[0]["calc_minutes"]

    @property
    def extra_state_attributes(self):
        """Return schedule attributes, filtering out old buses."""
        valid_trips = self._get_valid_trips()
        attrs = {
            "stop_id": self._stop_id,
            "buses": [] 
        }

        if valid_trips:
            # Set 'next' attributes based on the first valid trip
            next_bus = valid_trips[0]
            attrs["next_route"] = next_bus.get("routeShortName")
            attrs["next_destination"] = next_bus.get("tripHeadsign")
            attrs["next_time"] = next_bus.get("departureTime")[:5]

            # Build the clean list
            for trip in valid_trips:
                attrs["buses"].append({
                    "route": trip.get("routeShortName"),
                    "destination": trip.get("tripHeadsign"),
                    "time": trip.get("departureTime")[:5],
                    "minutes": trip["calc_minutes"]
                })

        return attrs
