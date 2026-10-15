import pytest

from conftest import CARD, commit, good_evidence
from playbook.gate import evaluate


def codes(r, base, head, ev):
    d = evaluate(r, base, head, ev)
    assert (d.verdict == "ALLOW") == (d.codes == [])
    assert d.codes == sorted(d.codes)
    return d.codes


def test_happy_path_allows(happy):
    r, base, head = happy
    assert codes(r, base, head, good_evidence(head)) == []


def test_executor_edits_test(happy):
    r, base, _ = happy
    head = commit(r, "executor", {"tests/test_slug.py": "def test_x():\n    pass\n"})
    assert "EXECUTOR_TOUCHED_TESTS" in codes(r, base, head, good_evidence(head))


def test_executor_edits_card(happy):
    r, base, _ = happy
    head = commit(r, "executor", {".delivery/DEMO-1.md": CARD + "\nmore\n"})
    assert "EXECUTOR_TOUCHED_TESTS" in codes(r, base, head, good_evidence(head))


def test_out_of_scope(happy):
    r, base, _ = happy
    head = commit(r, "executor", {"src/other.py": "x = 1\n"})
    assert "PATH_VIOLATION" in codes(r, base, head, good_evidence(head))


def test_budget_lines(happy):
    r, base, _ = happy
    head = commit(r, "executor", {"src/slug.py": "".join(f"x{i} = {i}\n" for i in range(60))})
    assert "BUDGET_EXCEEDED" in codes(r, base, head, good_evidence(head))


def test_budget_files(repo):
    r, base = repo
    card = CARD.replace("  - README.md\n", "  - README.md\n  - src/*\n").replace("max_files: 2", "max_files: 1")
    commit(r, "architect", {".delivery/DEMO-1.md": card})
    commit(r, "architect", {"tests/test_slug.py": "def test_x():\n    assert True\n"})
    head = commit(r, "executor", {"src/a.py": "a = 1\n", "src/b.py": "b = 1\n"})
    assert "BUDGET_EXCEEDED" in codes(r, base, head, good_evidence(head))


def test_card_not_first(repo):
    r, base = repo
    commit(r, "architect", {"tests/test_slug.py": "def test_x():\n    assert True\n"})
    commit(r, "architect", {".delivery/DEMO-1.md": CARD})
    head = commit(r, "executor", {"src/slug.py": "y = 1\n"})
    assert "CARD_NOT_FIRST" in codes(r, base, head, good_evidence(head))


def test_tests_after_impl(repo):
    r, base = repo
    commit(r, "architect", {".delivery/DEMO-1.md": CARD})
    commit(r, "executor", {"src/slug.py": "y = 1\n"})
    head = commit(r, "architect", {"tests/test_slug.py": "def test_x():\n    assert True\n"})
    assert "RED_TESTS_NOT_FIRST" in codes(r, base, head, good_evidence(head))


def test_signed_old_commit_then_pushed(happy):
    r, base, signed = happy
    head = commit(r, "executor", {"src/slug.py": "def slug(s):\n    return s.strip().lower()\n"})
    ev = good_evidence(head)
    ev["signoff"] = {"head": signed, "by": "owner"}
    assert codes(r, base, head, ev) == ["SIGNOFF_STALE"]


@pytest.mark.parametrize("key,patch,code", [
    ("review", None, "REVIEW_MISSING"),
    ("review", {"head": "0" * 40, "p1": 0}, "REVIEW_STALE"),
    ("review", "P1", "REVIEW_P1_OPEN"),
    ("ci", None, "CI_MISSING"),
    ("ci", {"head": "0" * 40, "status": "pass"}, "CI_STALE"),
    ("ci", "FAIL", "CI_FAILED"),
    ("signoff", None, "SIGNOFF_MISSING"),
    ("signoff", "AGENT", "SIGNOFF_NOT_OWNER"),
    ("signoff", "garbage", "SIGNOFF_MISSING"),
])
def test_evidence_codes(happy, key, patch, code):
    r, base, head = happy
    ev = good_evidence(head)
    if patch is None:
        del ev[key]
    elif patch == "P1":
        ev[key]["p1"] = 1
    elif patch == "FAIL":
        ev[key]["status"] = "fail"
    elif patch == "AGENT":
        ev[key]["by"] = "executor"
    elif patch == "garbage":
        ev[key] = "not-a-dict"
    else:
        ev[key] = patch
    assert codes(r, base, head, ev) == [code]
