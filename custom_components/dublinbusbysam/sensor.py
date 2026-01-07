"""Sensor platform for Dublin Bus by Sam."""
from __future__ import annotations
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_STOP_ID, CONF_FILTER_ROUTES

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    stop_id = entry.data[CONF_STOP_ID]
    
    # Parse the filter (e.g., "H3, 6" -> ["H3", "6"])
    filter_input = entry.data.get(CONF_FILTER_ROUTES, "")
    allowed_routes = [r.strip() for r in filter_input.split(",") if r.strip()] if filter_input else []

    entities = []
    
    # 1. Main "Next Bus" Sensor
    entities.append(DublinBusMainSensor(coordinator, stop_id, allowed_routes))
    
    # 2. Detail Sensors (Route, Destination, Time)
    entities.append(DublinBusDetailSensor(coordinator, stop_id, allowed_routes, "route"))
    entities.append(DublinBusDetailSensor(coordinator, stop_id, allowed_routes, "destination"))
    entities.append(DublinBusDetailSensor(coordinator, stop_id, allowed_routes, "time"))

    # 3. Individual Route Sensors (If filtering is used, create sensors for those routes. 
    # If no filter, we could dynamically create them, but for v2 let's stick to the filter list 
    # or just the main ones to avoid creating 50 sensors for busy stops automatically.)
    if allowed_routes:
        for route in allowed_routes:
            entities.append(DublinBusRouteSensor(coordinator, stop_id, route))

    async_add_entities(entities)


class DublinBusBase(CoordinatorEntity, SensorEntity):
    """Base class for all Dublin Bus sensors."""
    
    def __init__(self, coordinator, stop_id):
        super().__init__(coordinator)
        self._stop_id = stop_id

    def _get_valid_trips(self, allowed_routes=None):
        """Filter trips by time and optional route list."""
        trips = self.coordinator.data.get("upcomingTrips", [])
        valid_trips = []
        now = dt_util.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_seconds = (now - midnight).total_seconds()

        for trip in trips:
            # 1. Check Route Filter
            if allowed_routes and trip.get("routeShortName") not in allowed_routes:
                continue

            # 2. Check Time
            departure_timestamp = trip.get("departureTimestamp")
            if departure_timestamp is None:
                continue
            
            diff_seconds = departure_timestamp - current_seconds
            minutes = int(diff_seconds / 60)

            if minutes >= -1:
                trip["calc_minutes"] = max(0, minutes)
                valid_trips.append(trip)
                
        return valid_trips


class DublinBusMainSensor(DublinBusBase):
    """The main 'Minutes until next bus' sensor."""

    def __init__(self, coordinator, stop_id, allowed_routes):
        super().__init__(coordinator, stop_id)
        self._allowed_routes = allowed_routes
        self._attr_name = f"Dublin Bus {stop_id} Next Bus"
        self._attr_unique_id = f"dublin_bus_{stop_id}_main"
        self._attr_icon = "mdi:bus-clock"
        self._attr_unit_of_measurement = "min"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        trips = self._get_valid_trips(self._allowed_routes)
        return trips[0]["calc_minutes"] if trips else None

    @property
    def extra_state_attributes(self):
        """Keep the full list in attributes for the card."""
        trips = self._get_valid_trips(self._allowed_routes)
        attrs = {"buses": []}
        for trip in trips:
            attrs["buses"].append({
                "route": trip.get("routeShortName"),
                "destination": trip.get("tripHeadsign"),
                "time": trip.get("departureTime")[:5],
                "minutes": trip["calc_minutes"]
            })
        return attrs


class DublinBusDetailSensor(DublinBusBase):
    """Sensors for Next Route, Destination, or Time."""

    def __init__(self, coordinator, stop_id, allowed_routes, info_type):
        super().__init__(coordinator, stop_id)
        self._allowed_routes = allowed_routes
        self._info_type = info_type # 'route', 'destination', or 'time'
        
        friendly_type = info_type.capitalize()
        self._attr_name = f"Dublin Bus {stop_id} Next {friendly_type}"
        self._attr_unique_id = f"dublin_bus_{stop_id}_next_{info_type}"
        
        if info_type == "time":
            self._attr_icon = "mdi:clock-outline"
        elif info_type == "destination":
            self._attr_icon = "mdi:sign-direction"
        else:
            self._attr_icon = "mdi:bus"

    @property
    def native_value(self):
        trips = self._get_valid_trips(self._allowed_routes)
        if not trips:
            return "No Service"
        
        next_bus = trips[0]
        if self._info_type == "route":
            return next_bus.get("routeShortName")
        elif self._info_type == "destination":
            return next_bus.get("tripHeadsign")
        elif self._info_type == "time":
            return next_bus.get("departureTime")[:5]


class DublinBusRouteSensor(DublinBusBase):
    """A specific sensor for ONE route (e.g. Next H3)."""

    def __init__(self, coordinator, stop_id, route):
        super().__init__(coordinator, stop_id)
        self._route = route
        self._attr_name = f"Dublin Bus {stop_id} Route {route}"
        self._attr_unique_id = f"dublin_bus_{stop_id}_route_{route}"
        self._attr_icon = "mdi:bus"
        self._attr_unit_of_measurement = "min"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        # We pass ONLY this specific route to the filter
        trips = self._get_valid_trips([self._route])
        return trips[0]["calc_minutes"] if trips else None
