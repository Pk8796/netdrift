from netdrift.inventory import load_inventory

SAMPLE = """
defaults:
  username: admin
  password: admin
  platform: cisco_ios
devices:
  - name: r1
    host: 127.0.0.1
    port: 2211
  - name: r2
    host: 127.0.0.1
    port: 2212
    protected: true
    region: us-west
"""


def test_defaults_merge(tmp_path):
    inv = tmp_path / "inventory.yml"
    inv.write_text(SAMPLE)
    devices = load_inventory(inv)

    assert len(devices) == 2
    r1, r2 = devices
    assert r1.username == "admin"
    assert r1.platform == "cisco_ios"
    assert r1.protected is False
    assert r2.protected is True


def test_unknown_keys_land_in_extra(tmp_path):
    inv = tmp_path / "inventory.yml"
    inv.write_text(SAMPLE)
    _, r2 = load_inventory(inv)
    assert r2.extra["region"] == "us-west"
