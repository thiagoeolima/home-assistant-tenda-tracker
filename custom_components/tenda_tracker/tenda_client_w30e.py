import logging
import aiohttp
from datetime import datetime
import json
from .dataclass import Status, Firmware, Device
import ipaddress
import base64

logger = logging.getLogger(__name__)

class TendaClientW30E:
    _AUTH_DATA = ""

    def __init__(
        self, session: aiohttp.ClientSession, host="http://192.168.2.1", password=None
    ):
        self.host = host
        self.password = password
        self.session = session
        self._timeout = 60
        self._URLS = {
            "login": self.host + "/goform/module",
            "logout": self.host + "/goform/logout",
            "GetSysInfo": self.host + "/goform/module?getSysInfo&",
            "GetOnlineList": self.host + "/goform/module?getQosUserList&getQosPolicy&",
            "GetLanInfo": self.host + "/goform/module?getLanInfo&",
        }

    async def authorize(self):
        sample_string_bytes = self.password.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        self._AUTH_DATA = (
            '{"auth":{"password":"'
            + base64_string
            + '","time":"'
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + '"}}'
        )
        rep = await self.session.post(
            self._URLS["login"],
            data=self._AUTH_DATA,
            allow_redirects=False,
            raise_for_status=True,
        )
        assert rep.status == 200, f"Invalid http status code: {rep.status}"
        return True

    async def logout(self):
        r = await self.session.get(
            self._URLS["logout"],
            allow_redirects=False,
            raise_for_status=True,
        )
        assert r.status == 302, f"Get request: Invalid http status code: {r.status}"
        return True

    async def _req_post_json(self, url: str, data: str):
        resp = await self.session.post(
            url=url,
            data=data,
            allow_redirects=False,
            raise_for_status=True,
        )
        assert resp.status == 200, f"Invalid http status code: {resp.status}"
        body = await resp.text()
        return json.loads(body) if body else None

    async def get_status(self) -> Status:
        await self.authorize()
        onlineList = await self.get_online_list()
        devices = []
        wired_total = 0
        wifi_clients_total = 0
        wifi_2_clients_total = 0
        wifi_5_clients_total = 0
        offline_clients_total = 0
        for host in onlineList:
            if host["hostConnectType"] == 2:
                wired_total = wired_total + 1
            if host["hostConnectType"] == 3:
                wifi_clients_total = wifi_clients_total + 1
                wifi_2_clients_total = wifi_2_clients_total + 1
            if host["hostConnectType"] == 4:
                wifi_clients_total = wifi_clients_total + 1
                wifi_5_clients_total = wifi_5_clients_total + 1
            devices.append(
                Device(
                    id=host["ID"],
                    macaddr=host["hostMAC"],
                    hostname=host["hostRemark"]
                    if host["hostRemark"]
                    else host["hostName"],
                    ipaddr=ipaddress.ip_address(host["hostIP"]),
                    online=True,
                    type=host["hostConnectType"],
                )
            )
        offlineList = await self.get_offline_list()
        for host in offlineList:
            offline_clients_total = offline_clients_total + 1
            devices.append(
                Device(
                    id=host["ID"],
                    macaddr=host["hostMAC"],
                    hostname=host["hostRemark"]
                    if host["hostRemark"]
                    else host["hostName"],
                    ipaddr=ipaddress.ip_address(host["hostIP"]),
                    online=False,
                    host_offline_time=host["hostOffLineTime"],
                )
            )
        status = Status()
        lan_info = await self.get_lan_info()
        status.wan_macaddr = lan_info["lanMac"]
        sysInfo = await self.get_sys_info()
        status.mem_usage = sysInfo["memoryUsePercent"]
        status.cpu_usage = sysInfo["cpuUsePercent"]
        status.devices = devices
        status.clients_total = len(devices)
        status.offline_clients_total = offline_clients_total
        status.wired_total = wired_total
        status.wifi_clients_total = wifi_clients_total
        status.wifi_2_clients_total = wifi_2_clients_total
        status.wifi_5_clients_total = wifi_5_clients_total
        await self.logout()
        return status

    async def get_firmware(self) -> Firmware:
        sysInfo = await self.get_sys_info()
        return Firmware(
            firmware=sysInfo["sysInfoSoftVersion"],
            model=sysInfo["sysInfoDevName"],
            hardware=sysInfo["sysInfoSoftVersion"],
        )

    async def get_online_list(self) -> list:
        resp = await self._req_post_json(
            self._URLS["GetOnlineList"],
            data=('{"getQosUserList":{"type":1}}'),
        )
        return resp["getQosUserList"] if resp else None

    async def get_offline_list(self) -> list:
        resp = await self._req_post_json(
            self._URLS["GetOnlineList"],
            data=('{"getQosUserList":{"type":2}}'),
        )
        return resp["getQosUserList"] if resp else None

    async def get_sys_info(self):
        resp = await self._req_post_json(
            self._URLS["GetSysInfo"], data=('{"getSysInfo":""}')
        )
        return resp["getSysInfo"] if resp else None

    async def get_lan_info(self):
        resp = await self._req_post_json(
            self._URLS["GetLanInfo"], data=('{"getLanInfo":""}')
        )
        return resp["getLanInfo"] if resp else None
