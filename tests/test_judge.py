from types import SimpleNamespace

from services.judge import judge


def make_method(limit_type, min_val=None, max_val=None):
    return SimpleNamespace(limit_type=limit_type, min_val=min_val, max_val=max_val)


def test_presence_absence_pass():
    method = make_method("PresenceAbsence")
    assert judge(None, "Absent", method) == "Pass"


def test_presence_absence_fail():
    method = make_method("PresenceAbsence")
    assert judge(None, "Present", method) == "Fail"


def test_max_limit():
    method = make_method("Max", max_val=10)
    assert judge(9, None, method) == "Pass"
    assert judge(11, None, method) == "Fail"


def test_min_limit():
    method = make_method("Min", min_val=5)
    assert judge(6, None, method) == "Pass"
    assert judge(4, None, method) == "Fail"


def test_range_limit():
    method = make_method("Range", min_val=1, max_val=3)
    assert judge(2, None, method) == "Pass"
    assert judge(4, None, method) == "Fail"


def test_missing_value_returns_review():
    method = make_method("Max", max_val=10)
    assert judge(None, None, method) == "Review"
