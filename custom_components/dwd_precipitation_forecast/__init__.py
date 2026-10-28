"""The DWD Precipitation Forecast integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import DwdPrecipitationForecastCoordinator, DwdPrecipitationTypeCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up DWD Precipitation Forecast from a config entry."""

    coordinator = DwdPrecipitationForecastCoordinator(hass)

    await coordinator.async_config_entry_first_refresh()
    coordinator.type_coordinator = DwdPrecipitationTypeCoordinator(hass)
    # Ein fehlendes HymecNG-Produkt darf die bestehende Integration nicht verhindern.
    await coordinator.type_coordinator.async_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
