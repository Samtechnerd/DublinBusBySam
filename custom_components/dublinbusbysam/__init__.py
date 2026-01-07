"""The Dublin Bus by Sam integration."""
from __future__ import annotations

import logging
import async_timeout
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_STOP_ID, BASE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dublin Bus by Sam from a config entry."""
    
    stop_id = entry.data[CONF_STOP_ID]
    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from API."""
        try:
            async with async_timeout.timeout(10):
                url = BASE_URL.format(stop_id)
                resp = await session.get(url)
                resp.raise_for_status()
                data = await resp.json()
                return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Bus Stop {stop_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
