"""The EZSP Counters integration."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.components.zha.core.const import DATA_ZHA, DATA_ZHA_GATEWAY
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from .config_flow import NoZhaIntegration, validate_input
from .const import CONF_COUNTERS_ID, DOMAIN

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the EZSP Counters component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EZSP Counters from a config entry."""

    try:
        await validate_input(hass)
    except NoZhaIntegration:
        _LOGGER.error("No Zha integration or EZSP radio found")
        return False

    zha_gw = hass.data.get(DATA_ZHA, {}).get(DATA_ZHA_GATEWAY)
    if not zha_gw:
        _LOGGER.error("Where is the EZSP radio gone?")
        raise ConfigEntryNotReady

    try:
        state = getattr(zha_gw.application_controller, "state")
        counters = state.counters[CONF_COUNTERS_ID]
    except (KeyError, AttributeError):
        _LOGGER.error("EZSP radio does not have counters, needs an update?")
        return False

    hass.data[DOMAIN] = {CONF_COUNTERS_ID: counters}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
