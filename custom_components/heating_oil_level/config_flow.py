"""Config flow for Heating Oil Level integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    CONF_ENERGY_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_KWH_PER_LITRE,
    DEFAULT_TANK_CAPACITY,
    DEFAULT_KWH_PER_LITRE,
)

_LOGGER = logging.getLogger(__name__)


class HeatingOilLevelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heating Oil Level."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the energy entity exists
            energy_entity = user_input[CONF_ENERGY_ENTITY]
            state = self.hass.states.get(energy_entity)

            if state is None:
                errors["base"] = "entity_not_found"
            else:
                # Create unique ID based on energy entity
                await self.async_set_unique_id(f"heating_oil_{energy_entity}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Oil Tank ({energy_entity})",
                    data=user_input,
                )

        # Build the schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ENERGY_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="energy",
                    )
                ),
                vol.Required(
                    CONF_TANK_CAPACITY, default=DEFAULT_TANK_CAPACITY
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100,
                        max=10000,
                        step=50,
                        unit_of_measurement="L",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_KWH_PER_LITRE, default=DEFAULT_KWH_PER_LITRE
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=8.0,
                        max=12.0,
                        step=0.01,
                        unit_of_measurement="kWh/L",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HeatingOilLevelOptionsFlow(config_entry)


class HeatingOilLevelOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Heating Oil Level."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Return options data (don't modify entry.data)
            return self.async_create_entry(title="", data=user_input)

        # Merge data and options (options take precedence)
        current_config = {**self.config_entry.data, **(self.config_entry.options or {})}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_CAPACITY,
                    default=current_config.get(
                        CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100,
                        max=10000,
                        step=50,
                        unit_of_measurement="L",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_KWH_PER_LITRE,
                    default=current_config.get(
                        CONF_KWH_PER_LITRE, DEFAULT_KWH_PER_LITRE
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=8.0,
                        max=12.0,
                        step=0.01,
                        unit_of_measurement="kWh/L",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
