"""Config flow for Dublin Bus by Sam integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_STOP_ID, CONF_FILTER_ROUTES

class DublinBusBySamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dublin Bus by Sam."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title=f"Stop {user_input[CONF_STOP_ID]}", 
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required(CONF_STOP_ID, default="Stop-ID-here"): str,
            # New optional field for comma-separated routes
            vol.Optional(CONF_FILTER_ROUTES): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
