import time
from datetime import datetime, timezone
from pathlib import Path

from . import metrics
from .device import DeviceSession, Unreachable
from .drift import config_diff, has_drift, render_diff, summarize

BACKUP_DIR = Path("backups")


def _intended_for(device, intended_dir):
    return Path(intended_dir, f"{device.name}.cfg").read_text()


def _backup(device, running):
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"{device.name}-{stamp}.cfg"
    path.write_text(running)
    return path


def check_device(device, intended_dir):
    """Read-only drift check (Rung 1). Returns (diff, running)."""
    intended = _intended_for(device, intended_dir)
    with DeviceSession(device) as sess:
        running = sess.running_config()
    return config_diff(intended, running), running


def heal_device(device, intended_dir):
    """Detect and, if drifted, correct (Rung 2).

    Backs up the live config before touching anything, then verifies the push
    actually converged. If the push fails or doesn't converge, revert to the
    backup so we never leave a half-applied config behind.
    """
    intended = _intended_for(device, intended_dir)
    with DeviceSession(device) as sess:
        running = sess.running_config()
        diff = config_diff(intended, running)
        if not has_drift(diff):
            return "clean", diff

        _backup(device, running)
        try:
            sess.push(intended.splitlines())
            sess.save()
        except Exception:
            sess.push(running.splitlines())
            return "rollback", diff

        if has_drift(config_diff(intended, sess.running_config())):
            sess.push(running.splitlines())
            return "rollback", diff
        return "healed", diff


def reconcile_pass(devices, intended_dir, auto_heal, emit_metrics):
    for device in devices:
        started = time.monotonic()
        try:
            if auto_heal:
                status, diff = heal_device(device, intended_dir)
            else:
                diff, _ = check_device(device, intended_dir)
                status = "drift" if has_drift(diff) else "clean"
        except Unreachable as exc:
            print(f"[{device.name}] unreachable: {exc}")
            if emit_metrics:
                metrics.device_up.labels(device.name).set(0)
            continue

        if emit_metrics:
            metrics.device_up.labels(device.name).set(1)
            metrics.last_reconcile.labels(device.name).set(time.time())
            metrics.reconcile_seconds.labels(device.name).set(
                time.monotonic() - started
            )

        if status == "clean":
            print(f"[{device.name}] clean")
            continue

        if emit_metrics:
            metrics.drift_events_total.labels(device.name).inc()
            if status in ("healed", "rollback"):
                metrics.reconciles_total.labels(device.name, status).inc()

        added, removed = summarize(diff)
        print(f"[{device.name}] {status} (+{added} / -{removed})")
        print(render_diff(diff))


def run_loop(devices, intended_dir, interval, auto_heal, emit_metrics):
    while True:
        reconcile_pass(devices, intended_dir, auto_heal, emit_metrics)
        time.sleep(interval)
