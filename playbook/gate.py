"""Check committed scope, authorship, budget, and head-bound evidence."""

from dataclasses import dataclass
from fnmatch import fnmatchcase
import re
import subprocess

from .card import CardError, parse_card


@dataclass
class Decision:
    verdict: str
    codes: list[str]


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        capture_output=True, text=True,
    ).stdout


def protected(path):
    return path.startswith(("tests/", ".delivery/"))


def evidence_codes(evidence, head):
    codes = set()
    for key, field, expected, failure in (
        ("review", "p1", 0, "P1_OPEN"),
        ("ci", "status", "pass", "FAILED"),
        ("signoff", "by", "owner", "NOT_OWNER"),
    ):
        item = evidence.get(key) if isinstance(evidence, dict) else None
        valid = isinstance(item, dict) and isinstance(item.get("head"), str) and bool(item["head"])
        value = item.get(field) if isinstance(item, dict) else None
        valid = valid and (
            (type(value) is int and value >= 0) if key == "review"
            else (isinstance(value, str) and bool(value))
        )
        if not valid:
            codes.add(f"{key.upper()}_MISSING")
            continue
        if item["head"] != head:
            codes.add(f"{key.upper()}_STALE")
        if value != expected:
            codes.add(f"{key.upper()}_{failure}")
    return codes


def evaluate(repo, base, head, evidence) -> Decision:
    head = git(repo, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
    codes = evidence_codes(evidence, head)
    commits = git(repo, "rev-list", "--reverse", "--topo-order", f"{base}..{head}").splitlines()
    changes = []
    roles = []
    files = set()
    line_count = 0
    card_path = None
    for commit in commits:
        paths = git(repo, "diff-tree", "--root", "--no-commit-id", "-r", "--no-renames", "--name-only", "-z", commit).split("\0")
        paths = [path for path in paths if path]
        if not changes and len(paths) == 1 and paths[0].startswith(".delivery/"):
            card_path = paths[0]
        changes.append(paths)
        message = git(repo, "show", "-s", "--format=%B", commit)
        role_lines = re.findall(r"^Role: (architect|executor)$", message, re.MULTILINE)
        role = role_lines[0] if len(role_lines) == 1 else None
        roles.append(role)
        if role is None:
            codes.add("ROLE_MISSING")
        if role == "executor" and any(protected(path) for path in paths):
            codes.add("EXECUTOR_TOUCHED_TESTS")
        for entry in git(repo, "diff-tree", "--root", "--no-commit-id", "-r", "--no-renames", "--numstat", "-z", commit).split("\0"):
            if not entry:
                continue
            added, deleted, path = entry.split("\t", 2)
            if not path.startswith("tests/") and path != card_path:
                files.add(path)
                if added == "-" or deleted == "-":
                    codes.add("BUDGET_EXCEEDED")
                else:
                    line_count += int(added) + int(deleted)
    card = None
    if changes and len(changes[0]) == 1:
        path = changes[0][0]
        if path.startswith(".delivery/") and path.endswith(".md"):
            try:
                card = parse_card(git(repo, "show", f"{commits[0]}:{path}"))
                if path != f".delivery/{card.task}.md":
                    codes.add("CARD_NOT_FIRST")
            except (CardError, subprocess.CalledProcessError):
                codes.add("CARD_NOT_FIRST")
    if card is None:
        codes.add("CARD_NOT_FIRST")
    if len(changes) < 2 or roles[1] != "architect" or not changes[1] or any(
        not path.startswith("tests/") for path in changes[1]
    ):
        codes.add("RED_TESTS_NOT_FIRST")
    if card is not None:
        if any(not any(fnmatchcase(path, pattern) for pattern in card.allowed_paths) for path in files):
            codes.add("PATH_VIOLATION")
        if len(files) > card.max_files or line_count > card.max_lines:
            codes.add("BUDGET_EXCEEDED")
    return Decision("BLOCK" if codes else "ALLOW", sorted(codes))
