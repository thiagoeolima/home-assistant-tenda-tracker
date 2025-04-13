from ipaddress import IPv4Address
from dataclasses import dataclass


@dataclass
class Firmware:
    def __init__(self, hardware: str, model: str, firmware: str) -> None:
        self.hardware_version = hardware
        self.model = model
        self.firmware_version = firmware


@dataclass
class Device:
    def __init__(
        self,
        id: str,
        macaddr: str,
        ipaddr: IPv4Address,
        hostname: str,
        online: bool,
        type: str = None,
        host_offline_time: str = None,
    ) -> None:
        self.id = id
        self.type = type
        self._macaddr = macaddr
        self._ipaddr = ipaddr
        self.hostname = hostname
        self.host_offline_time = host_offline_time
        self.online = online

    @property
    def macaddr(self):
        return str(self._macaddr)

    @property
    def macaddress(self):
        return self._macaddr

    @property
    def ipaddr(self):
        return str(self._ipaddr)

    @property
    def ipaddress(self):
        return self._ipaddr


@dataclass
class Status:
    def __init__(self) -> None:
        self.wan_macaddr: str | None = None
        self.wired_total: int = 0
        self.wifi_clients_total: int = 0
        self.wifi_5_clients_total: int = 0
        self.wifi_2_clients_total: int = 0
        self.clients_total: int = 0
        self.offline_clients_total: int = 0
        self.mem_usage: float | None = None
        self.cpu_usage: float | None = None
        self.devices: list[Device] = []
