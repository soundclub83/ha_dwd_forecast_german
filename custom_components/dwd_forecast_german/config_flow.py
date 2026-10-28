"""Config flow for DWD Precipitation Forecast integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Koordinaten und Standortnamen prüfen."""
    if not data["name"].strip() or not (-90 <= data[CONF_LATITUDE] <= 90 and -180 <= data[CONF_LONGITUDE] <= 180):
        raise ValueError("Ungültige Standortangaben")
    return {"title": data["name"].strip()}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DWD Precipitation Forecast."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_coordinates"
            except Exception:
                _LOGGER.exception("Fehler bei der Einrichtung")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default=self.hass.config.location_name): str,
                vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): float,
                vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): float,
            }),
            errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
