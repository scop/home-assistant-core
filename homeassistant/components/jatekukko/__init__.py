"""The jatekukko integration."""
from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import NamedTuple

import aiohttp
from pytekukko import Pytekukko
from pytekukko.models import InvoiceHeader, Service as PytekukkoService

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_CUSTOMER_NUMBER, DEFAULT_UPDATE_INTERVAL, DOMAIN, LOGGER

PLATFORMS = [
    Platform.CALENDAR,
    Platform.SENSOR,
]

# https://www.jatekukko.fi/media/kuvat/jatekukko/logot/jatekukko_logo.svg
# https://www.jatekukko.fi/media/kuvat/jatekukko/logot/jatekukko_logo_valk.svg


class ServiceData(NamedTuple):
    """Container for a Jätekukko service instance."""

    service: PytekukkoService
    collection_schedule: list[date]


class JatekukkoData(NamedTuple):
    """Container for Jätekukko integration wide data."""

    service_datas: dict[int, ServiceData]
    invoice_headers: list[InvoiceHeader]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up jatekukko from a config entry."""

    client = Pytekukko(
        async_get_clientsession(hass),
        customer_number=entry.data[CONF_CUSTOMER_NUMBER],
        password=entry.data[CONF_PASSWORD],
    )

    async def get_data() -> JatekukkoData:
        service_data = {}
        try:
            services = await client.get_services()
        except aiohttp.ClientResponseError as ex:
            if ex.status == HTTPStatus.UNAUTHORIZED:
                raise ConfigEntryAuthFailed from ex
            raise
        for service in services:
            # TODO: do not fetch for disabled service entities?
            collection_schedule = await client.get_collection_schedule(service)
            service_data[service.pos] = ServiceData(service, collection_schedule)
        invoice_headers = await client.get_invoice_headers()
        return JatekukkoData(service_data, invoice_headers)

    coordinator = DataUpdateCoordinator[JatekukkoData](
        hass,
        LOGGER,
        name=f"Customer number {entry.data[CONF_CUSTOMER_NUMBER]}",
        update_interval=DEFAULT_UPDATE_INTERVAL,
        update_method=get_data,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator, client

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        _, client = hass.data[DOMAIN].pop(entry.entry_id)
        try:
            await client.logout()
        except Exception:  # pylint: disable=broad-except
            LOGGER.debug("Could not logout", exc_info=True)

    return unload_ok
