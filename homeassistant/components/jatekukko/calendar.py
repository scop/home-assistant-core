"""Jätekukko calendar entries."""
from __future__ import annotations

import datetime
from typing import cast

from pytekukko.models import InvoiceHeader

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import JatekukkoData, ServiceData
from .const import CONF_CUSTOMER_NUMBER, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jätekukko calendar entries based on a config entry."""
    coordinator, _ = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        JatekukkoCollectionCalendar(coordinator, entry, service_data)
        for _, service_data in coordinator.data.service_datas.items()
        if service_data.collection_schedule
    )
    async_add_entities([JatekukkoInvoiceCalendar(coordinator, entry)])


class JatekukkoCollectionCalendar(CoordinatorEntity, CalendarEntity):
    """Jätekukko collection calendar."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[JatekukkoData],
        entry: ConfigEntry,
        service_data: ServiceData,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)

        self._pos = service_data.service.pos

        self._attr_name = service_data.service.name
        self._attr_unique_id = f"{self._pos}@{entry.data[CONF_CUSTOMER_NUMBER]}"
        self.collection_schedule = sorted(service_data.collection_schedule)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Respond to a DataUpdateCoordinator update."""
        self.update_from_latest_data()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the state."""

        service_data = self.coordinator.data.service_datas.get(self._pos)
        if not service_data:
            self._attr_available = False
            self.collection_schedule.clear()
            return

        self._attr_available = True
        self.collection_schedule = sorted(service_data.collection_schedule)

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        today = datetime.date.today()
        for date in self.collection_schedule:
            if date >= today:
                return CalendarEvent(date, date, cast(str, self.name))
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        start_date_date = start_date.date()
        end_date_date = end_date.date()

        matching_dates = filter(
            lambda date: start_date_date <= date < end_date_date,
            self.collection_schedule,
        )

        return [
            CalendarEvent(date, date, cast(str, self.name)) for date in matching_dates
        ]


class JatekukkoInvoiceCalendar(CoordinatorEntity, CalendarEntity):
    """Jätekukko invoice calendar."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[JatekukkoData],
        entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = "Jätekukko invoices"
        self._attr_unique_id = f"invoices@{entry.data[CONF_CUSTOMER_NUMBER]}"
        self.invoice_headers: list[InvoiceHeader] = []

    @callback
    def _handle_coordinator_update(self) -> None:
        """Respond to a DataUpdateCoordinator update."""
        self.update_from_latest_data()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the state."""
        self.invoice_headers = sorted(
            self.coordinator.data.invoice_headers,
            key=lambda invoice_header: cast(datetime.date, invoice_header.due_date),
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        today = datetime.date.today()
        for invoice_header in self.invoice_headers:
            if invoice_header.due_date >= today:
                return CalendarEvent(
                    invoice_header.due_date,
                    invoice_header.due_date,
                    invoice_header.name,
                )
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        start_date_date = start_date.date()
        end_date_date = end_date.date()

        matching_invoice_headers = filter(
            lambda invoice_header: start_date_date
            <= invoice_header.due_date
            < end_date_date,
            self.invoice_headers,
        )

        return [
            CalendarEvent(
                invoice_header.due_date, invoice_header.due_date, invoice_header.name
            )
            for invoice_header in matching_invoice_headers
        ]
