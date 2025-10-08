import requests
import datetime
from homeassistant.helpers.entity import Entity
from google.transit import gtfs_realtime_pb2

API_URL = "https://api.nationaltransport.ie/gtfsr/v2/gtfsr/tripUpdates"
API_KEY = "b9d5cee3e4ae44709ede9c6fe7d17f06"  # replace with your National Transport API key

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Dublin Bus sensor."""
    stopid = config.get("stopid")
    if not stopid:
        return

    add_entities([DublinBusSensor(stopid)], True)


class DublinBusSensor(Entity):
    """Representation of a Dublin Bus sensor."""

    def __init__(self, stopid):
        self._stopid = stopid
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return f"Dublin Bus {self._stopid}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    def update(self):
        """Fetch new state data for the sensor."""
        try:
            headers = {"x-api-key": API_KEY}
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)

            arrivals = []
            for entity in feed.entity:
                if entity.HasField("trip_update"):
                    for stop_time_update in entity.trip_update.stop_time_update:
                        if stop_time_update.stop_id == self._stopid:
                            arrival_time = stop_time_update.arrival.time
                            dt = datetime.datetime.fromtimestamp(arrival_time)
                            arrivals.append(dt.strftime("%H:%M"))

            arrivals.sort()
            if arrivals:
                self._state = arrivals[0]
                self._attributes["next_arrivals"] = arrivals[1:5]  # next 4 buses
            else:
                self._state = "No buses"
                self._attributes = {}

        except Exception as e:
            self._state = "Error"
            self._attributes = {"error": str(e)}
