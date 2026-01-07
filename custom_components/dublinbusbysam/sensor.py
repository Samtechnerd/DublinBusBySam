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

    @property
    def native_value(self):
        """Return minutes until next bus."""
        trips = self.coordinator.data.get("upcomingTrips", [])
        if not trips:
            return None 

        return self._calculate_minutes(trips[0].get("departureTimestamp"))

    @property
    def extra_state_attributes(self):
        """Return full schedule attributes."""
        trips = self.coordinator.data.get("upcomingTrips", [])
        attrs = {
            "stop_id": self._stop_id,
            "buses": [] 
        }

        if trips:
            next_bus = trips[0]
            attrs["next_route"] = next_bus.get("routeShortName")
            attrs["next_destination"] = next_bus.get("tripHeadsign")
            attrs["next_time"] = next_bus.get("departureTime")[:5]

            for trip in trips:
                attrs["buses"].append({
                    "route": trip.get("routeShortName"),
                    "destination": trip.get("tripHeadsign"),
                    "time": trip.get("departureTime")[:5],
                    "minutes": self._calculate_minutes(trip.get("departureTimestamp"))
                })

        return attrs

    def _calculate_minutes(self, departure_timestamp):
        """Calculate minutes between now and timestamp."""
        if departure_timestamp is None:
            return 0
        now = dt_util.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_seconds = (now - midnight).total_seconds()
        diff = departure_timestamp - current_seconds
        return max(0, int(diff / 60))
