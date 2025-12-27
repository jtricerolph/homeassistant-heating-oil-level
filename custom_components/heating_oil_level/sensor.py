"""Sensor platform for Heating Oil Level integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfVolume, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_ENERGY_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_KWH_PER_LITRE,
    DEFAULT_KWH_PER_LITRE,
    ATTR_LAST_READING,
    ATTR_LAST_READING_DATE,
    ATTR_ENERGY_AT_READING,
    ATTR_OIL_CONSUMED,
    ATTR_TANK_CAPACITY,
)
from . import async_save_data

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heating Oil Level sensors."""
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    data = hass.data[DOMAIN][entry.entry_id]["data"]

    entities = [
        OilLevelSensor(hass, entry, config, data),
        OilPercentageSensor(hass, entry, config, data),
        OilConsumedSensor(hass, entry, config, data),
        OilRemainingLitresSensor(hass, entry, config, data),
    ]

    async_add_entities(entities)


class OilLevelBaseSensor(SensorEntity, RestoreEntity):
    """Base class for oil level sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._config = config
        self._data = data
        self._energy_entity = config["energy_entity"]
        self._tank_capacity = config["tank_capacity"]
        self._kwh_per_litre = config.get("kwh_per_litre", DEFAULT_KWH_PER_LITRE)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Heating Oil Tank",
            manufacturer="Custom",
            model="Oil Level Monitor",
        )

    def _get_current_energy(self) -> float | None:
        """Get the current energy reading from the boiler entity."""
        state = self.hass.states.get(self._energy_entity)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _calculate_oil_consumed(self) -> float | None:
        """Calculate oil consumed since last reading."""
        if self._data.get("energy_at_reading") is None:
            return None

        current_energy = self._get_current_energy()
        if current_energy is None:
            return None

        energy_used = current_energy - self._data["energy_at_reading"]
        if energy_used < 0:
            # Energy meter might have reset, use 0
            energy_used = 0

        oil_consumed = energy_used / self._kwh_per_litre
        return round(oil_consumed, 2)

    def _calculate_current_level(self) -> float | None:
        """Calculate current oil level in litres."""
        if self._data.get("last_reading") is None:
            return None

        oil_consumed = self._calculate_oil_consumed()
        if oil_consumed is None:
            return self._data["last_reading"]

        current_level = self._data["last_reading"] - oil_consumed
        return max(0, round(current_level, 2))

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Track state changes of the energy entity
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._energy_entity],
                self._async_energy_state_changed,
            )
        )

    @callback
    def _async_energy_state_changed(self, event) -> None:
        """Handle energy entity state changes."""
        self.async_write_ha_state()


class OilLevelSensor(OilLevelBaseSensor):
    """Sensor for current oil level in litres."""

    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:oil"
    _attr_name = "Oil Level"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, config, data)
        self._attr_unique_id = f"{entry.entry_id}_oil_level"

    @property
    def native_value(self) -> float | None:
        """Return the current oil level."""
        return self._calculate_current_level()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            ATTR_LAST_READING: self._data.get("last_reading"),
            ATTR_LAST_READING_DATE: self._data.get("last_reading_date"),
            ATTR_ENERGY_AT_READING: self._data.get("energy_at_reading"),
            ATTR_OIL_CONSUMED: self._calculate_oil_consumed(),
            ATTR_TANK_CAPACITY: self._tank_capacity,
        }


class OilPercentageSensor(OilLevelBaseSensor):
    """Sensor for oil level as percentage."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gauge"
    _attr_name = "Oil Level Percentage"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, config, data)
        self._attr_unique_id = f"{entry.entry_id}_oil_percentage"

    @property
    def native_value(self) -> float | None:
        """Return the current oil level as percentage."""
        current_level = self._calculate_current_level()
        if current_level is None:
            return None
        percentage = (current_level / self._tank_capacity) * 100
        return round(min(100, max(0, percentage)), 1)


class OilConsumedSensor(OilLevelBaseSensor):
    """Sensor for oil consumed since last reading."""

    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:fire"
    _attr_name = "Oil Consumed Since Reading"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, config, data)
        self._attr_unique_id = f"{entry.entry_id}_oil_consumed"

    @property
    def native_value(self) -> float | None:
        """Return oil consumed since last reading."""
        return self._calculate_oil_consumed()


class OilRemainingLitresSensor(OilLevelBaseSensor):
    """Sensor showing remaining litres until empty."""

    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:oil-level"
    _attr_name = "Oil Remaining"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, config, data)
        self._attr_unique_id = f"{entry.entry_id}_oil_remaining"

    @property
    def native_value(self) -> float | None:
        """Return remaining oil level."""
        return self._calculate_current_level()
