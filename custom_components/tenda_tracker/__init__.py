from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .coordinator import TendaRouterCoordinator
from .tenda_client_w30e import TendaClientW30E
import logging
from homeassistant.helpers.aiohttp_client import (
    SERVER_SOFTWARE,
    async_create_clientsession,
)
import aiohttp

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Construct the device
    host = entry.data[CONF_HOST]
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "http://{}".format(host)
    jar = aiohttp.CookieJar(unsafe=True)
    session = async_create_clientsession(hass, False, cookie_jar=jar)

    client = TendaClientW30E(
        host=host, password=entry.data[CONF_PASSWORD], session=session
    )
    await client.authorize()
    firmware = await client.get_firmware()
    status = await client.get_status()
    await client.logout()
    # Create device coordinator and fetch data
    coordinator = TendaRouterCoordinator(
        hass,
        client,
        entry.data[CONF_SCAN_INTERVAL],
        firmware,
        status,
        _LOGGER,
        entry.entry_id,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(config_entry.entry_id)
