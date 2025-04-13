from __future__ import annotations
from datetime import timedelta
from logging import Logger
from collections.abc import Callable
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from .tenda_client_w30e import TendaClientW30E
from .const import (
    DOMAIN,
    DEFAULT_NAME,
)
from .dataclass import Status, Firmware


class TendaRouterCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        router: TendaClientW30E,
        update_interval: int,
        firmware: Firmware,
        status: Status,
        logger: Logger,
        unique_id: str,
    ) -> None:
        self.router = router
        self.unique_id = unique_id
        self.status = status
        self.device_info = DeviceInfo(
            configuration_url=router.host,
            connections={(CONNECTION_NETWORK_MAC, self.status.wan_macaddr)},
            identifiers={(DOMAIN, self.status.wan_macaddr)},
            manufacturer="Tenda",
            model=firmware.model,
            name=DEFAULT_NAME,
            sw_version=firmware.firmware_version,
            hw_version=firmware.hardware_version,
        )

        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Asynchronous update of all data."""
        self.status = await self.router.get_status()
