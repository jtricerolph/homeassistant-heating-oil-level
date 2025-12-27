"""Constants for the Heating Oil Level integration."""

DOMAIN = "heating_oil_level"

# Configuration keys
CONF_ENERGY_ENTITY = "energy_entity"
CONF_TANK_CAPACITY = "tank_capacity"
CONF_KWH_PER_LITRE = "kwh_per_litre"

# Default values
DEFAULT_TANK_CAPACITY = 1000  # litres
DEFAULT_KWH_PER_LITRE = 10.35  # kWh per litre of heating oil

# Storage keys
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1

# Attributes
ATTR_LAST_READING = "last_reading"
ATTR_LAST_READING_DATE = "last_reading_date"
ATTR_ENERGY_AT_READING = "energy_at_reading"
ATTR_OIL_CONSUMED = "oil_consumed"
ATTR_TANK_CAPACITY = "tank_capacity"

# Platforms
PLATFORMS = ["sensor", "number"]
