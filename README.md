# NetDrift — GitOps for the Network

Repo: https://github.com/Pk8796/netdrift

> It's Argo CD, but for routers: declare the network you want in Git, and a loop keeps the real devices matching it, healing config drift on its own.

A small Python control loop that keeps network devices matching an **intended configuration declared in Git**. It reads each device's live config, detects **drift** from the declared state, and either reports it or auto-corrects it — with drift events exported to Prometheus/Grafana.

Config drift is the silent gap between what a device's config *should* be and what it *actually* is, usually from an out-of-band manual change nobody wrote down. In real networks that gap causes outages nobody can trace. NetDrift closes it with the same reconciliation-loop idea GitOps tools use for Kubernetes — one layer down, on network gear.

## How it works

```
 Git repo (intended config — single source of truth)
 ├── inventory.yml        devices + connection info
 ├── intended/r1.cfg      desired config per device
 └── templates/*.j2       (optional) render configs from a data model
          │  reads intended state
          ▼
 reconciliation loop  ──SSH (Netmiko)──▶  virtual lab (containerlab / FRR)
   1. pull running config                     r1   r2   r3
   2. diff vs intended
   3. report or auto-heal (+ backup/rollback)
          │  emits drift metrics
          ▼
 Prometheus + Grafana  (drift events, per-device health)
```

## Quick start

```bash
git clone https://github.com/Pk8796/netdrift.git
cd netdrift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Bring up the lab (needs Docker + [containerlab](https://containerlab.dev)):

```bash
make lab-up
```

> FRR containers need `sshd` and vtysh reachable on port 22. Once they're up and
> the intended configs are applied, the SSH ports map to `127.0.0.1:2211-2213` as
> declared in `inventory.yml`.

### Rung 1 — detect drift (read-only)

```bash
netdrift check
```

Exits non-zero if any device has drifted, so CI can use it directly. Change a
setting on a router by hand, run it again, and it prints exactly what drifted.

### Rung 2 — self-heal

```bash
netdrift reconcile --auto-heal --once      # single pass
netdrift reconcile --auto-heal             # continuous loop (default 30s)
```

On drift it backs up the live config to `backups/`, pushes the intended config,
verifies the device converged, and rolls back to the backup if the push fails or
doesn't take. This is the headline demo: fat-finger a VLAN or interface
description, watch the loop notice and revert it within seconds.

### Rung 3 — observe

```bash
netdrift reconcile --auto-heal --metrics   # metrics on :9808/metrics
```

Point Prometheus at it (`observability/prometheus.yml`) and import
`observability/grafana-dashboard.json`. Panels: drift rate, per-device drift
count, reachability, time since last reconcile.

## Intent-based config (optional)

Instead of hand-writing each `intended/*.cfg`, generate them from a small data
model:

```bash
netdrift render                 # devices.vars.yml + templates/frr.cfg.j2 -> intended/
```

## Layout

```
netdrift/        control loop (inventory, device I/O, drift, reconcile, metrics, cli)
intended/        desired config per device — the source of truth
templates/       Jinja2 config templates
lab/             containerlab topology
observability/   prometheus config + grafana dashboard
tests/           pytest (drift + inventory logic, no network needed)
```

## Notes / tradeoffs

- Netmiko keeps the loop vendor-neutral and simple. For production-grade
  replace-and-commit with native rollback, NAPALM's `load_replace_candidate` /
  `commit` is the natural upgrade — the `DeviceSession` wrapper is the seam.
- `netdrift check` is what CI runs on every PR to the intended-config repo, so
  network changes get reviewed like code.

## License

MIT
