"""The EZSP Counters integration."""

import asyncio
import logging
from typing import Dict

from aiohttp import web
from zigpy import state as app_state
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.zha.core.const import DATA_ZHA, DATA_ZHA_GATEWAY
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import HTTP_INTERNAL_SERVER_ERROR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
import voluptuous as vol

from .config_flow import NoZhaIntegration, check_for_ezsp_zha
from .const import CONF_ENABLE_ENTITIES, CONF_ENABLE_HTTP, CONF_URL_ID, DOMAIN, DATA_DEV_COUNTERS, DATA_COUNTERS

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)
URL_COUNTERS_ID = "/api/" + DOMAIN + "/{counters_id}"

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the EZSP Counters component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EZSP Counters from a config entry."""

    try:
        await check_for_ezsp_zha(hass)
    except NoZhaIntegration:
        _LOGGER.error("No Zha integration or EZSP radio found")
        return False

    zha_gw = hass.data.get(DATA_ZHA, {}).get(DATA_ZHA_GATEWAY)
    if not zha_gw:
        _LOGGER.error("Where is the EZSP radio gone?")
        raise ConfigEntryNotReady

    try:
        state = getattr(zha_gw.application_controller, "state")
    except (KeyError, AttributeError):
        _LOGGER.error("EZSP radio does not have counters, needs an update?")
        return False

    hass.data[DOMAIN] = state

    if entry.data[CONF_ENABLE_ENTITIES]:
        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )

    if entry.data[CONF_ENABLE_HTTP]:
        host = get_url(hass, prefer_external=False, allow_cloud=False)
        uri = URL_COUNTERS_ID.format(counters_id=entry.data[CONF_URL_ID])
        _LOGGER.info("registering %s%s url for counter view", host, uri)
        hass.http.register_view(
            CountersWebView(state, entry.data[CONF_URL_ID])
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


class CountersWebView(HomeAssistantView):
    """Expose counters via http endpoint."""

    url = URL_COUNTERS_ID
    name = f"api:{DOMAIN}"
    requires_auth = False
    cors_allowed = True

    def __init__(self, state: app_state.State, url_id: str) -> None:
        """Initialize instance."""
        self._state: app_state.State = state
        self._url_id: str = url_id

    async def get(self, request: web.Request, counters_id: str) -> web.Response:
        """Process get request."""

        if counters_id != self._url_id:
            return web.Response(status=HTTP_INTERNAL_SERVER_ERROR)

        resp = [
            {
                "collection": counters.name,
                "counter": counter.name,
                "value": counter.value,
                "resets": counter.reset_count,
            }
            for counters in self._state.counters.values()
            for counter in counters
        ]

        return self.json(resp)
