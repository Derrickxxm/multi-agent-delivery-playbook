import json
from pathlib import Path

from playbook.council import validate

GOOD = {
    "round1": {"model-a": "x", "model-b": "y", "model-c": "z"},
    "round2_positions": {"A": "fixed hold only", "B": "add one stop", "C": "no stops"},
    "devils_advocate": "model-b",
    "disagreements": [{"id": "D1", "ruling": "one stop variant"}],
}


def test_good():
    assert validate(GOOD) == []


def test_not_anonymized():
    bad = {**GOOD, "round2_positions": {"A": "model-a says fixed hold", "B": "y", "C": "z"}}
    assert "NOT_ANONYMIZED" in validate(bad)


def test_no_devils_advocate():
    assert "NO_DEVILS_ADVOCATE" in validate({**GOOD, "devils_advocate": "someone-else"})


def test_unruled():
    assert "UNRULED" in validate({**GOOD, "disagreements": [{"id": "D1", "ruling": ""}]})


def test_too_few():
    assert "TOO_FEW_MEMBERS" in validate({**GOOD, "round1": {"model-a": "x", "model-b": "y"}})


def test_example_doc_is_valid():
    rec = json.loads((Path(__file__).parents[1] / "docs" / "council-example.json").read_text())
    assert validate(rec) == []
