import pytest

from conftest import CARD
from playbook.card import CardError, load_card


def test_load_card(tmp_path):
    p = tmp_path / "c.md"
    p.write_text(CARD)
    c = load_card(p)
    assert (c.task, c.allowed_paths, c.max_files, c.max_lines) == ("DEMO-1", ["src/slug.py", "README.md"], 2, 40)


@pytest.mark.parametrize("drop", ["task:", "max_files:", "max_lines:", "allowed_paths:"])
def test_missing_field(tmp_path, drop):
    p = tmp_path / "c.md"
    p.write_text("\n".join(l for l in CARD.splitlines() if not l.startswith(drop)))
    with pytest.raises(CardError):
        load_card(p)
