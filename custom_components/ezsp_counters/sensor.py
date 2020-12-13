"""Sensor Entity for EZSP counters."""

from datetime import timedelta
import logging
from typing import Any, Callable, Dict, Optional

from bellows.zigbee.state import Counter, Counters

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity
from homeassistant.helpers.typing import HomeAssistantType

from .const import CONF_COUNTERS_ID, DOMAIN

ATTR_RESET_COUNT = "reset_count"
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=20)


async def async_setup_entry(
    hass: HomeAssistantType, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up the Zigbee Home Automation sensor from config entry."""

    counters: Counters = hass.data[DOMAIN][CONF_COUNTERS_ID]
    entities = [EzspCounter(counter) for counter in counters]
    async_add_entities(entities)


class EzspCounter(entity.Entity):
    """EZSP Counter Entity."""

    def __init__(self, counter: Counter) -> None:
        """Initialize entity."""
        self._counter = counter

    @property
    def unique_id(self) -> Optional[str]:
        """Return Unique ID of the sensor."""
        return self._counter.name

    @property
    def state(self) -> Optional[int]:
        """Return current counter value."""
        return self._counter.value

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """State attributes."""
        return {ATTR_RESET_COUNT: self._counter.reset_count}

    @property
    def should_poll(self) -> bool:
        """Return True to make it poll."""
        return True

    async def async_update(self) -> None:
        """Retrieve latest state."""
        self.async_write_ha_state()
