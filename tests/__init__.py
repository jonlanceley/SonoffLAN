import asyncio
import threading
from typing import List

from homeassistant.config_entries import HomeAssistant  # fix circular import
from homeassistant.helpers.entity import Entity

from custom_components.sonoff.core.entity import XEntity
from custom_components.sonoff.core.ewelink import SIGNAL_ADD_ENTITIES, XRegistry

DEVICEID = "1000123abc"


class DummyRegistry(XRegistry):
    def __init__(self):
        # noinspection PyTypeChecker
        super().__init__(None)
        self.send_args = None

    async def send(self, *args, **kwargs):
        self.send_args = args

    def call(self, coro):
        asyncio.get_event_loop().run_until_complete(coro)
        return self.send_args


# noinspection PyTypeChecker
def init(device: dict, config: dict = None) -> (XRegistry, List[XEntity]):
    devices = [device] if isinstance(device, dict) else device
    for device in devices:
        device.setdefault("name", "Device1")
        device.setdefault("deviceid", DEVICEID)
        device.setdefault("online", True)
        device.setdefault("extra", {"uiid": 0})
        params = device.setdefault("params", {})
        params.setdefault("staMac", "FF:FF:FF:FF:FF:FF")

    asyncio.create_task = lambda _: None
    asyncio.get_running_loop = lambda: type("", (), {"_thread_id": threading.get_ident()})

    entities = []

    reg = DummyRegistry()
    reg.cloud.online = True
    reg.config = config
    reg.dispatcher_connect(SIGNAL_ADD_ENTITIES, lambda x: entities.extend(x))
    entities += reg.setup_devices(devices)

    try:
        hass = HomeAssistant("")  # new Hass
    except TypeError:
        hass = HomeAssistant()  # old Hass

    for entity in entities:
        if not isinstance(entity, Entity):
            continue
        entity.hass = hass
        entity.async_write_ha_state()

    return reg, entities


def save_to(store: list):
    return lambda *args, **kwargs: store.append({**dict(enumerate(args)), **kwargs})
