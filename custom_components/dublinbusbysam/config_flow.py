"""Config flow for Dublin Bus by Sam integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_STOP_ID, CONF_FILTER_ROUTES, CONF_FRIENDLY_NAME

class DublinBusBySamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dublin Bus by Sam."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Use the friendly name as the title if provided, otherwise use Stop ID
            title = user_input.get(CONF_FRIENDLY_NAME) or f"Stop {user_input[CONF_STOP_ID]}"
            return self.async_create_entry(
                title=title, 
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required(CONF_STOP_ID, default="8240DB003721"): str,
            vol.Optional(CONF_FRIENDLY_NAME): str,  # New Optional Name Field
            vol.Optional(CONF_FILTER_ROUTES): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
