from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


class Unreachable(Exception):
    pass


class DeviceSession:
    """Thin context manager around one netmiko connection.

    Kept simple on purpose. If you want proper replace-and-commit with rollback,
    NAPALM is the drop-in here — this class is the seam.
    """

    def __init__(self, device):
        self.device = device
        self._conn = None

    def __enter__(self):
        params = {
            "device_type": self.device.platform,
            "host": self.device.host,
            "port": self.device.port,
            "username": self.device.username,
            "password": self.device.password,
            "fast_cli": False,
        }
        try:
            self._conn = ConnectHandler(**params)
        except (NetmikoTimeoutException, NetmikoAuthenticationException, OSError) as exc:
            raise Unreachable(f"{self.device.name}: {exc}") from exc
        return self

    def __exit__(self, *_exc):
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def running_config(self):
        return self._conn.send_command(self.device.show_run_cmd, read_timeout=30)

    def push(self, config_lines):
        return self._conn.send_config_set(config_lines, read_timeout=60)

    def save(self):
        try:
            self._conn.save_config()
        except (NotImplementedError, ValueError):
            # not every platform in the lab implements copy run start cleanly
            pass
