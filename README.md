# NetDrift

A small tool I built to catch and fix **config drift** on network devices — the
same "keep reality matching Git" idea GitOps uses for Kubernetes, pointed at
routers instead. Built the week after my CCNA to turn the cert into something
that actually runs.

Repo: https://github.com/Pk8796/netdrift

## The problem it solves

Someone SSHes into a router, changes a setting, and forgets to write it down.
Now the device's real config quietly disagrees with what everyone *thinks* it
is. That gap is config drift, and in real networks it's behind a lot of outages
nobody can trace back.

NetDrift keeps the intended config for every device in Git (the source of truth)
and runs a loop that compares each device against it — then either tells you
what drifted or pushes the correct config back on its own.

## What it does

- SSHes into each device and pulls the running config
- diffs it against the intended config in `intended/`
- reports the drift, exiting non-zero so CI can gate on it
- with `--auto-heal`, backs up the live config, pushes the intended one, and
  rolls back if the push fails or doesn't take
- exports drift metrics to Prometheus so you can watch it on Grafana

It's the same reconciliation-loop idea as Argo CD, one layer down on network gear.

## Running it

```bash
git clone https://github.com/Pk8796/netdrift.git
cd netdrift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

You need a lab of virtual devices to point it at. Either works — the code is the
same, only `inventory.yml` changes:

- **containerlab** (lighter, all free): `make lab-up` (needs Docker)
- **GNS3** (real IOS/EOS images): steps in [docs/gns3-setup.md](docs/gns3-setup.md)

Then:

```bash
netdrift check                            # just detect drift (read-only)
netdrift reconcile --auto-heal --once     # detect + fix, single pass
netdrift reconcile --auto-heal --metrics  # continuous loop, metrics on :9808
```

For the metrics, point Prometheus at `observability/prometheus.yml` and import
`observability/grafana-dashboard.json` into Grafana.

Optional — generate the intended configs from a small data model instead of
hand-writing them:

```bash
netdrift render
```

## The demo

Log into a router by hand and break something — change an interface description
or an IP. The loop notices within seconds, backs up the live config, reverts it
to what Git says, and the drift event spikes then clears on Grafana. That's the
30-second clip worth recording.

## Layout

```
netdrift/        the actual tool (inventory, ssh, diff, reconcile, metrics, cli)
intended/        desired config per device — source of truth
templates/       Jinja2 templates for generating configs
lab/             containerlab topology
observability/   prometheus config + grafana dashboard
docs/            gns3 setup
tests/           pytest for the diff + inventory logic (no network needed)
```

## Notes

- I used Netmiko because it's simple and vendor-neutral. The natural upgrade is
  NAPALM, which gives you native replace-and-commit with rollback — the
  `DeviceSession` class in `device.py` is the seam to swap it in.
- The tests cover the pure logic (drift detection, inventory parsing) since
  those don't need a live device. The device-facing bits you verify by running
  against the lab.
- CI (`.github/workflows/drift-check.yml`) runs lint + tests on every PR, and
  `netdrift check` is meant to run on PRs to the intended-config repo so network
  changes get reviewed like code.

## License

MIT
