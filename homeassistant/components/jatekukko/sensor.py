"""Jätekukko sensors."""
from __future__ import annotations

from pytekukko.models import Service as PytekukkoService

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import JatekukkoData
from .const import CONF_CUSTOMER_NUMBER, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jätekukko sensors based on a config entry."""
    coordinator, _ = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        JatekukkoNextCollectionSensor(coordinator, entry, service_data.service)
        for _, service_data in coordinator.data.service_datas.items()
        if service_data.service.next_collection
    )


class JatekukkoNextCollectionSensor(CoordinatorEntity, SensorEntity):
    """Jätekukko Sensor."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[JatekukkoData],
        entry: ConfigEntry,
        service: PytekukkoService,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._pos = service.pos

        self.entity_description = SensorEntityDescription(
            key="next_collection",
            name=service.name,
            device_class=SensorDeviceClass.DATE,
        )
        self._attr_unique_id = f"{self._pos}@{entry.data[CONF_CUSTOMER_NUMBER]}"
        self._attr_device_info = DeviceInfo(
            configuration_url="https://tilasto.jatekukko.fi/indexservice2.jsp",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.data[CONF_CUSTOMER_NUMBER])},
            manufacturer="Jätekukko",
            model="Omakukko",
        )

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
            return

        self._attr_available = True
        self._attr_native_value = service_data.service.next_collection
