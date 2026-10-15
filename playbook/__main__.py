"""Run isolated, reproducible examples without network access."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from .gate import evaluate, git


CARD = """---
task: DEMO-1
allowed_paths:
  - src/*
max_files: 2
max_lines: 40
---
Implement a synthetic greeting.
"""


def commit(repo, role, files):
    for name, contents in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        git(repo, "add", "--", name)
    git(repo, "commit", "-q", "-m", f"Synthetic change\n\nRole: {role}")
    return git(repo, "rev-parse", "HEAD").strip()


def demo():
    scenarios = {
        "happy": [],
        "executor edits test": ["EXECUTOR_TOUCHED_TESTS"],
        "out of scope": ["PATH_VIOLATION"],
        "budget": ["BUDGET_EXCEEDED"],
        "stale signoff": ["SIGNOFF_STALE"],
        "stale review": ["REVIEW_STALE"],
        "ci failed": ["CI_FAILED"],
        "tests after implementation": ["RED_TESTS_NOT_FIRST"],
    }
    success = True
    print("scenario | expected | actual codes")
    print("--- | --- | ---")
    with TemporaryDirectory(prefix="playbook-") as temp:
        for index, (name, expected) in enumerate(scenarios.items()):
            repo = Path(temp) / str(index)
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Synthetic demo")
            git(repo, "config", "user.email", "noreply@example.invalid")
            git(repo, "config", "commit.gpgsign", "false")
            base = commit(repo, "architect", {"README.md": "Synthetic demo\n"})
            commit(repo, "architect", {".delivery/DEMO-1.md": CARD})
            red = {"tests/test_greeting.py": "def test_greeting():\n    assert greeting() == 'hello'\n"}
            implementation = {"src/greeting.py": "def greeting():\n    return 'hello'\n"}
            if name == "tests after implementation":
                commit(repo, "executor", implementation)
                head = commit(repo, "architect", red)
            else:
                commit(repo, "architect", red)
                head = commit(repo, "executor", implementation)
            original = head
            attacks = {
                "executor edits test": {"tests/test_greeting.py": "def test_greeting():\n    pass\n"},
                "out of scope": {"other.py": "outside = True\n"},
                "budget": {"src/greeting.py": "value = 1\n" * 50},
                "stale signoff": {"src/greeting.py": "def greeting():\n    return 'hello again'\n"},
            }
            if name in attacks:
                head = commit(repo, "executor", attacks[name])
            evidence = {
                "review": {"head": head, "p1": 0},
                "ci": {"head": head, "status": "pass"},
                "signoff": {"head": head, "by": "owner"},
            }
            if name == "stale signoff":
                evidence["signoff"]["head"] = original
            if name == "stale review":
                evidence["review"]["head"] = base
            if name == "ci failed":
                evidence["ci"]["status"] = "fail"
            decision = evaluate(repo, base, head, evidence)
            matches = decision.codes == expected and decision.verdict == ("BLOCK" if expected else "ALLOW")
            success = success and matches
            print(f"{name} | {', '.join(expected) or 'ALLOW'} | {', '.join(decision.codes) or decision.verdict}")
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["demo"])
    parser.parse_args()
    return demo()


if __name__ == "__main__":
    raise SystemExit(main())
