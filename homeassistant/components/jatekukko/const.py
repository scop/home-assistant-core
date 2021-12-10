"""Constants for the jatekukko integration."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "jatekukko"

DEFAULT_UPDATE_INTERVAL: Final = timedelta(days=1)

CONF_CUSTOMER_NUMBER: Final = "customer_number"

LOGGER: Final = logging.getLogger(__package__)
