"""Config flow for Fireworks Tonight integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_POSTCODE, CONF_MAX_DISTANCE, DEFAULT_MAX_DISTANCE

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fireworks Tonight."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate postcode
            postcode = user_input[CONF_POSTCODE]
            if not postcode or not postcode.isdigit() or len(postcode) != 4:
                errors[CONF_POSTCODE] = "invalid_postcode"
            else:
                # Create the config entry
                return self.async_create_entry(
                    title=f"Fireworks Tonight - {postcode}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POSTCODE): str,
                    vol.Optional(
                        CONF_MAX_DISTANCE, default=DEFAULT_MAX_DISTANCE
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )