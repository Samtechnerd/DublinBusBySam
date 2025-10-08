from __future__ import annotations
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any

import requests
from google.transit import gtfs_realtime_pb2

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant

ATTR_STOP_ID = "Stop ID"
ATTR_ROUTE = "Route"
ATTR_DUE_IN = "Due in"
ATTR_DUE_AT = "Due at"
ATTR_NEXT_UP = "Later Bus"

SCAN_INTERVAL = timedelta(minutes=1)
TIME_STR_FORMAT = "%H:%M"

_RESOURCE = "https://api.nationaltransport.ie/gtfsr/v2/gtfsr/tripUpdates"
API_KEY = "b9d5cee3e4ae44709ede9c6fe7d17f06"


def due_in_minutes(timestamp):
    """Return minutes until timestamp."""
    diff = datetime.fromtimestamp(timestamp) - datetime.now()
    return str(int(diff.total_seconds() / 60))


def setup_platform(hass: HomeAssistant, config, add_entities, discovery_info=None):
    """Set up the Dublin Bus sensor."""
    stop = config.get("stopid")
    name = config.get("name", "Next Bus")
    add_entities([DublinBusSensor(stop, name)], True)


class DublinBusSensor(SensorEntity):
    """Implementation of a Dublin Bus sensor using GTFS-Realtime."""

    _attr_attribution = "Data provided by NTA GTFS-Realtime"
    _attr_icon = "mdi:bus"

    def __init__(self, stop, name):
        self._stop = stop
        self._name = name
        self._state = None
        self._times = []

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._times:
            next_up = "None"
            if len(self._times) > 1:
                next_up = f"{self._times[1][ATTR_ROUTE]} in {self._times[1][ATTR_DUE_IN]}"

            return {
                ATTR_DUE_IN: self._times[0][ATTR_DUE_IN],
                ATTR_DUE_AT: self._times[0][ATTR_DUE_AT],
                ATTR_STOP_ID: self._stop,
                ATTR_ROUTE: self._times[0][ATTR_ROUTE],
                ATTR_NEXT_UP: next_up,
            }
        return None

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.MINUTES

    def update(self):
        self._times = []
        try:
            headers = {"x-api-key": API_KEY}
            response = requests.get(_RESOURCE, headers=headers)
            response.raise_for_status()

            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)

            arrivals = []
            for entity in feed.entity:
                if entity.HasField("trip_update"):
                    for stop_time_update in entity.trip_update.stop_time_update:
                        if stop_time_update.stop_id == self._stop:
                            arrival_time = stop_time_update.arrival.time
                            dt = datetime.fromtimestamp(arrival_time)
                            arrivals.append({
                                ATTR_DUE_AT: dt.strftime(TIME_STR_FORMAT),
                                ATTR_ROUTE: entity.trip_update.trip.route_id,
                                ATTR_DUE_IN: due_in_minutes(arrival_time)
                            })

            arrivals.sort(key=lambda x: x[ATTR_DUE_IN])
            self._times = arrivals[:2]  # keep next 2 buses
            if self._times:
                self._state = self._times[0][ATTR_DUE_IN]
            else:
                self._state = "No buses"

        except Exception as e:
            self._state = "Error"
            self._times = [{ATTR_ROUTE: "N/A", ATTR_DUE_AT: "N/A", ATTR_DUE_IN: "N/A"}]

