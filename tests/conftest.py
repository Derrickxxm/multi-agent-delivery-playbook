import subprocess
from pathlib import Path

import pytest

CARD = """---
task: DEMO-1
allowed_paths:
  - src/slug.py
  - README.md
max_files: 2
max_lines: 40
---
Add a slugify helper.
"""


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo, role, files, msg="change"):
    for rel, text in files.items():
        p = Path(repo) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", f"{msg}\n\nRole: {role}")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.name", "t")
    git(r, "config", "user.email", "t@example.invalid")
    base = commit(r, "architect", {"README.md": "x\n"}, "base")
    return r, base


@pytest.fixture
def happy(repo):
    r, base = repo
    commit(r, "architect", {".delivery/DEMO-1.md": CARD}, "card")
    commit(r, "architect", {"tests/test_slug.py": "def test_x():\n    assert True\n"}, "red tests")
    head = commit(r, "executor", {"src/slug.py": "def slug(s):\n    return s.lower()\n"}, "impl")
    return r, base, head


def good_evidence(head):
    return {"review": {"head": head, "p1": 0}, "ci": {"head": head, "status": "pass"},
            "signoff": {"head": head, "by": "owner"}}
