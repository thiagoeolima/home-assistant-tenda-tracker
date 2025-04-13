from __future__ import annotations

from typing import Any, TypeAlias
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import TendaRouterCoordinator
from .dataclass import Device
from .const import (
    DOMAIN,
    EVENT_NEW_DEVICE,
    EVENT_ONLINE,
    EVENT_OFFLINE,
)

MAC_ADDR: TypeAlias = str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    tracked: dict[MAC_ADDR, TendaTracker] = {}

    @callback
    def coordinator_updated():
        """Update the status of the device."""
        update_items(coordinator, async_add_entities, tracked)

    entry.async_on_unload(coordinator.async_add_listener(coordinator_updated))
    coordinator_updated()


@callback
def update_items(
    coordinator: TendaRouterCoordinator,
    async_add_entities: AddEntitiesCallback,
    tracked: dict[MAC_ADDR, TendaTracker],
) -> None:
    """Update tracked device state from the hub."""
    new_tracked: list[TendaTracker] = []
    fire_event = tracked != {}

    for device in coordinator.status.devices:
        eventType = None
        if device.macaddr not in tracked:
            tracked[device.macaddr] = TendaTracker(coordinator, device)
            tracked[device.macaddr].active = device.online
            new_tracked.append(tracked[device.macaddr])
            eventType = EVENT_NEW_DEVICE
        else:
            tracked[device.macaddr].device = device
            if device.online and not tracked[device.macaddr].active:
                eventType = EVENT_ONLINE
            elif not device.online and tracked[device.macaddr].active:
                eventType = EVENT_OFFLINE
            tracked[device.macaddr].active = device.online

        if fire_event and eventType is not None:
            coordinator.hass.bus.fire(eventType, tracked[device.macaddr].data)

    if new_tracked:
        async_add_entities(new_tracked)


class TendaTracker(CoordinatorEntity, ScannerEntity):
    """Representation of network device."""

    def __init__(
        self,
        coordinator: TendaRouterCoordinator,
        data: Device,
    ) -> None:
        """Initialize the tracked device."""
        self.device = data
        self.active = False

        super().__init__(coordinator)

    @property
    def is_connected(self) -> bool:
        """Return true if the client is connected to the network."""
        return self.active

    @property
    def source_type(self) -> str:
        """Return the source type of the client."""
        return SourceType.ROUTER

    @property
    def name(self) -> str:
        """Return the name of the client."""
        return (
            self.device.hostname if self.device.hostname != "" else self.device.macaddr
        )

    @property
    def hostname(self) -> str:
        """Return the hostname of the client."""
        return self.device.hostname

    @property
    def mac_address(self) -> MAC_ADDR:
        """Return the mac address of the client."""
        return self.device.macaddr

    @property
    def ip_address(self) -> str:
        """Return the ip address of the client."""
        return self.device.ipaddr

    @property
    def unique_id(self) -> str:
        """Return an unique identifier for this device."""
        return f"{self.coordinator.unique_id}_{DOMAIN}_{self.mac_address}"

    @property
    def icon(self) -> str:
        """Return device icon."""
        return "mdi:lan-connect" if self.is_connected else "mdi:lan-disconnect"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attributes = {"id_roteador": self.device.id}
        if self.device.host_offline_time is not None:
            attributes["host_offline_time"] = self.device.host_offline_time
        return attributes

    @property
    def data(self) -> dict[str, str]:
        return dict(
            self.extra_state_attributes.items()
            | {
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "mac_address": self.mac_address,
            }.items()
        )

    @property
    def entity_registry_enabled_default(self) -> bool:
        return True
