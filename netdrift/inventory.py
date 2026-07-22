from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Device:
    name: str
    host: str
    username: str
    password: str
    platform: str = "cisco_ios"
    port: int = 22
    protected: bool = False
    show_run_cmd: str = "show running-config"
    extra: dict = field(default_factory=dict)


def load_inventory(path="inventory.yml"):
    raw = yaml.safe_load(Path(path).read_text())
    defaults = raw.get("defaults", {})

    fields = set(Device.__annotations__) - {"extra"}
    devices = []
    for entry in raw["devices"]:
        merged = {**defaults, **entry}
        known = {k: v for k, v in merged.items() if k in fields}
        extra = {k: v for k, v in merged.items() if k not in fields}
        devices.append(Device(extra=extra, **known))
    return devices
