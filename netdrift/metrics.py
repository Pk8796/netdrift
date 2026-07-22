from prometheus_client import Counter, Gauge, start_http_server

drift_events_total = Counter(
    "netdrift_drift_events_total", "Drift events detected", ["device"]
)
reconciles_total = Counter(
    "netdrift_reconciles_total", "Auto-corrections applied", ["device", "result"]
)
device_up = Gauge("netdrift_device_up", "Device reachable (1/0)", ["device"])
last_reconcile = Gauge(
    "netdrift_last_reconcile_timestamp", "Unix time of last reconcile pass", ["device"]
)
reconcile_seconds = Gauge(
    "netdrift_reconcile_duration_seconds", "Duration of last reconcile pass", ["device"]
)

_started = False


def serve(port=9808):
    global _started
    if not _started:
        start_http_server(port)
        _started = True
