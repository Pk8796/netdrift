import difflib

# Lines devices emit that mean nothing for comparison. Without stripping these,
# every read looks like drift because of a timestamp or a byte count.
_VOLATILE = (
    "Building configuration",
    "Current configuration",
    "! Last configuration change",
    "ntp clock-period",
)

_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"


def normalize(cfg: str) -> str:
    kept = []
    for line in cfg.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.lstrip().startswith(_VOLATILE):
            continue
        kept.append(line)
    return "\n".join(kept)


def config_diff(intended: str, running: str):
    a = normalize(intended).splitlines()
    b = normalize(running).splitlines()
    return list(
        difflib.unified_diff(a, b, fromfile="intended", tofile="running", lineterm="")
    )


def has_drift(diff) -> bool:
    for line in diff:
        if line[:1] in "+-" and not line.startswith(("+++", "---")):
            return True
    return False


def summarize(diff):
    added = removed = 0
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def render_diff(diff, color=True) -> str:
    if not color:
        return "\n".join(diff)
    out = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            out.append(f"{_GREEN}{line}{_RESET}")
        elif line.startswith("-") and not line.startswith("---"):
            out.append(f"{_RED}{line}{_RESET}")
        else:
            out.append(line)
    return "\n".join(out)
