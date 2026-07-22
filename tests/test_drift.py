from netdrift.drift import config_diff, has_drift, normalize, summarize

INTENDED = """hostname r1
!
interface eth1
 ip address 10.12.0.1/24
"""


def test_normalize_drops_volatile_and_blank_lines():
    raw = "Building configuration...\n\nhostname r1\n  \n"
    assert normalize(raw) == "hostname r1"


def test_identical_config_has_no_drift():
    assert not has_drift(config_diff(INTENDED, INTENDED))


def test_changed_line_is_drift():
    running = INTENDED.replace("10.12.0.1/24", "10.12.0.99/24")
    diff = config_diff(INTENDED, running)
    assert has_drift(diff)
    added, removed = summarize(diff)
    assert added == 1
    assert removed == 1


def test_trailing_whitespace_is_not_drift():
    running = INTENDED.replace("hostname r1", "hostname r1   ")
    assert not has_drift(config_diff(INTENDED, running))


def test_added_line_on_device_is_drift():
    running = INTENDED + " shutdown\n"
    assert has_drift(config_diff(INTENDED, running))
