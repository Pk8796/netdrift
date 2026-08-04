# Running NetDrift against a GNS3 lab

NetDrift doesn't care what's behind the SSH port — GNS3, containerlab, or real
gear. This guide covers the GNS3 path, which gives you real network OS images
(Arista vEOS, Cisco IOSv/IOL, FRR) that behave like production.

## What you need

- GNS3 + the GNS3 VM (both free).
- A device image. **Arista vEOS** is free with an Arista account and behaves
  like real EOS. FRR and VyOS are also free. (Cisco IOSv/IOL images are the ones
  with licensing friction — not required here.)

## Topology

Drop 2–3 routers on the canvas and cable them together on their data ports
(eth1/eth2), mirroring `intended/*.cfg`. Then give each one a **management path
back to your host** so host-side Python can SSH in — this is the only part that
trips people up.

Add a **Cloud** or **NAT** node and connect each router's management interface
to it. On vEOS that's `Management1`; on IOSv it's `GigabitEthernet0/0`. Put those
mgmt interfaces on a subnet your host can reach (the GNS3 NAT cloud hands out
something like `192.168.122.x`).

## Enable SSH on the devices

Each device needs an admin user and SSH on its management interface. On vEOS:

```
configure
username admin privilege 15 secret admin
management ssh
   no shutdown
interface Management1
   ip address 192.168.122.11/24
```

Repeat with `.12`, `.13` for the other nodes, and apply the rest of each
device's intended config so the first `netdrift check` comes back clean.

## Point NetDrift at it

Only `inventory.yml` changes — the code stays identical:

```yaml
defaults:
  username: admin
  password: admin
  platform: arista_eos    # or cisco_ios / frr, matching your image
  port: 22

devices:
  - name: r1
    host: 192.168.122.11
  - name: r2
    host: 192.168.122.12
  - name: r3
    host: 192.168.122.13
    protected: true
```

Then:

```bash
netdrift check                          # Rung 1
netdrift reconcile --auto-heal          # Rung 2
netdrift reconcile --auto-heal --metrics   # Rung 3
```

## The demo

SSH into a router in GNS3 and fat-finger something by hand — change an interface
description or an IP. The reconcile loop notices within seconds, backs up the
live config, pushes the intended config back, and the drift event spikes then
clears on the Grafana dashboard. That 30-second clip is the artifact worth
recording.

## Notes

- Real IOS/EOS implement `write memory` cleanly, so `save()` works and you can
  trim a couple of entries from `_VOLATILE` in `drift.py` if the platform's
  running-config is already stable.
- If SSH negotiation fails on older images, netmiko may need legacy KEX/cipher
  flags — set them in the connection params in `device.py` if you hit that.
