import argparse
import sys

from . import metrics, reconcile
from .drift import has_drift
from .inventory import load_inventory


def cmd_check(args):
    devices = load_inventory(args.inventory)
    drifted = []
    for device in devices:
        try:
            diff, _ = reconcile.check_device(device, args.intended)
        except reconcile.Unreachable as exc:
            print(f"[{device.name}] unreachable: {exc}")
            drifted.append(device.name)
            continue
        if has_drift(diff):
            drifted.append(device.name)
            print(f"[{device.name}] DRIFT")
            print(reconcile.render_diff(diff))
        else:
            print(f"[{device.name}] clean")

    if drifted:
        print(f"\ndrift on: {', '.join(drifted)}")
        return 1
    return 0


def cmd_reconcile(args):
    devices = load_inventory(args.inventory)
    if args.metrics:
        metrics.serve(args.metrics_port)
        print(f"metrics on :{args.metrics_port}/metrics")
    if args.once:
        reconcile.reconcile_pass(devices, args.intended, args.auto_heal, args.metrics)
        return 0
    reconcile.run_loop(
        devices, args.intended, args.interval, args.auto_heal, args.metrics
    )
    return 0


def cmd_render(args):
    from . import render

    for path in render.render_all(vars_file=args.vars):
        print(f"wrote {path}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="netdrift", description="GitOps for the network")
    p.add_argument("--inventory", default="inventory.yml")
    p.add_argument("--intended", default="intended")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="detect drift (read-only)")
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("reconcile", help="detect and optionally heal drift")
    r.add_argument("--auto-heal", action="store_true", help="push intended config back")
    r.add_argument("--once", action="store_true", help="single pass instead of a loop")
    r.add_argument("--interval", type=int, default=30, help="loop interval seconds")
    r.add_argument("--metrics", action="store_true", help="expose Prometheus metrics")
    r.add_argument("--metrics-port", type=int, default=9808)
    r.set_defaults(func=cmd_reconcile)

    d = sub.add_parser("render", help="render intended configs from templates")
    d.add_argument("--vars", default="devices.vars.yml")
    d.set_defaults(func=cmd_render)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
