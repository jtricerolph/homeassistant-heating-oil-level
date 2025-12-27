"""Number platform for Heating Oil Level integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_TANK_CAPACITY,
    DEFAULT_KWH_PER_LITRE,
)
from . import async_save_data

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heating Oil Level number entities."""
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    data = hass.data[DOMAIN][entry.entry_id]["data"]

    entities = [
        OilReadingInput(hass, entry, config, data),
    ]

    async_add_entities(entities)


class OilReadingInput(NumberEntity, RestoreEntity):
    """Number entity for inputting manual oil level readings."""

    _attr_has_entity_name = True
    _attr_name = "Manual Oil Reading"
    _attr_icon = "mdi:gauge-full"
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1.0
    _attr_native_min_value = 0

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._config = config
        self._data = data
        self._tank_capacity = config["tank_capacity"]
        self._energy_entity = config["energy_entity"]
        self._attr_unique_id = f"{entry.entry_id}_manual_reading"
        self._attr_native_max_value = float(self._tank_capacity)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Heating Oil Tank",
            manufacturer="Custom",
            model="Oil Level Monitor",
        )
        # Current value shown in the input
        self._value: float | None = None

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        # Show the last reading if available, otherwise None
        if self._data.get("last_reading") is not None:
            return float(self._data["last_reading"])
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        """Set a new oil level reading."""
        _LOGGER.info("Setting new oil reading: %s litres", value)

        # Get current energy reading to use as baseline
        energy_state = self.hass.states.get(self._energy_entity)
        current_energy = None
        if energy_state and energy_state.state not in ("unknown", "unavailable"):
            try:
                current_energy = float(energy_state.state)
            except (ValueError, TypeError):
                pass

        # Update the stored data
        self._data["last_reading"] = value
        self._data["last_reading_date"] = datetime.now().isoformat()
        self._data["energy_at_reading"] = current_energy
        self._value = value

        # Save to persistent storage
        await async_save_data(self.hass, self._entry.entry_id)

        # Update all entities
        self.async_write_ha_state()

        # Trigger sensor updates by firing an event
        self.hass.bus.async_fire(
            f"{DOMAIN}_reading_updated",
            {"entry_id": self._entry.entry_id, "reading": value},
        )

        _LOGGER.info(
            "Oil reading updated: %s L, energy baseline: %s kWh",
            value,
            current_energy,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in ("unknown", "unavailable"):
                try:
                    self._value = float(last_state.state)
                except (ValueError, TypeError):
                    pass
