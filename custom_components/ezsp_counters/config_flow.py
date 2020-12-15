"""Config flow for EZSP Counters integration."""
import logging
import uuid

from homeassistant import config_entries, core, exceptions
from homeassistant.components.zha.core.const import (
    DATA_ZHA,
    DATA_ZHA_GATEWAY,
    RadioType,
)

from .const import CONF_COUNTERS_ID, CONF_URL_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant) -> None:
    """Validate the user input allows us to connect."""

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    zha_gw = hass.data.get(DATA_ZHA, {}).get(DATA_ZHA_GATEWAY)
    if not zha_gw:
        _LOGGER.error("No zha integration or gateway found")
        raise NoZhaIntegration

    # check it is Ezsp radio
    if zha_gw.radio_description != RadioType.ezsp.description:
        _LOGGER.error("Only EZSP radio is supported")
        raise NoZhaIntegration

    try:
        state = getattr(zha_gw.application_controller, "state")
        state.counters[CONF_COUNTERS_ID]
    except (KeyError, AttributeError) as exc:
        _LOGGER.error("EZSP radio does not have counters, needs an update?")
        raise NoZhaIntegration from exc


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EZSP Counters."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        if self._async_current_entries() or self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        try:
            await validate_input(self.hass)
        except NoZhaIntegration:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title="EZSP Counters", data={CONF_URL_ID: uuid.uuid4()}
            )

        return self.async_abort(reason="No EZSP radio type")


class NoZhaIntegration(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
