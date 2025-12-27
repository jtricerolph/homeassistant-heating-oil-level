"""The Heating Oil Level integration."""
from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_ENERGY_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_KWH_PER_LITRE,
    DEFAULT_KWH_PER_LITRE,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

CARD_JS_URL = "/local/heating-oil-tank-card.js"
CARD_JS_FILE = "heating-oil-tank-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Heating Oil Level component."""
    # Copy the card JS to the www folder
    await hass.async_add_executor_job(_copy_card_to_www, hass)
    return True


def _copy_card_to_www(hass: HomeAssistant) -> None:
    """Copy the card JS file to Home Assistant www folder."""
    try:
        # Source path (in the integration folder)
        source = Path(__file__).parent / "www" / CARD_JS_FILE

        # Destination path (Home Assistant www folder)
        www_path = Path(hass.config.path("www"))
        www_path.mkdir(exist_ok=True)
        dest = www_path / CARD_JS_FILE

        # Copy if source exists and is newer or dest doesn't exist
        if source.exists():
            if not dest.exists() or source.stat().st_mtime > dest.stat().st_mtime:
                shutil.copy2(source, dest)
                _LOGGER.info("Copied heating oil tank card to %s", dest)
    except Exception as err:
        _LOGGER.warning("Could not copy card JS file: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heating Oil Level from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create storage for persistent data
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
    stored_data = await store.async_load()

    if stored_data is None:
        stored_data = {
            "last_reading": None,
            "last_reading_date": None,
            "energy_at_reading": None,
        }

    # Store configuration and data
    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "data": stored_data,
        "config": {
            "energy_entity": entry.data[CONF_ENERGY_ENTITY],
            "tank_capacity": entry.data.get(CONF_TANK_CAPACITY, 1000),
            "kwh_per_litre": entry.data.get(CONF_KWH_PER_LITRE, DEFAULT_KWH_PER_LITRE),
        },
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_save_data(hass: HomeAssistant, entry_id: str) -> None:
    """Save data to storage."""
    if entry_id in hass.data[DOMAIN]:
        store = hass.data[DOMAIN][entry_id]["store"]
        data = hass.data[DOMAIN][entry_id]["data"]
        await store.async_save(data)
