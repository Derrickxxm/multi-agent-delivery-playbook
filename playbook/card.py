"""Parse the deliberately small delivery-card front matter format."""

from dataclasses import dataclass
from pathlib import Path
import re


class CardError(ValueError):
    """The card cannot define a usable scope and budget."""


@dataclass
class Card:
    task: str
    allowed_paths: list[str]
    max_files: int
    max_lines: int


def load_card(path) -> Card:
    return parse_card(Path(path).read_text(encoding="utf-8"))


def parse_card(text: str) -> Card:
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise CardError("Missing front matter")
    fields = {}
    listing = False
    for line in lines[1:lines.index("---", 1)]:
        if listing and re.fullmatch(r"  - .+", line):
            fields["allowed_paths"].append(line[4:].strip())
            continue
        listing = False
        match = re.fullmatch(r"(task|allowed_paths|max_files|max_lines):\s*(.*)", line)
        if not match:
            if line.strip():
                raise CardError("Unsupported front matter")
            continue
        key, value = match.groups()
        if key in fields:
            raise CardError(f"Duplicate field: {key}")
        if key == "allowed_paths":
            if value:
                raise CardError("allowed_paths must be a list")
            fields[key] = []
            listing = True
        else:
            fields[key] = value
    for key in ("task", "allowed_paths", "max_files", "max_lines"):
        if not fields.get(key):
            raise CardError(f"Missing field: {key}")
    for key in ("max_files", "max_lines"):
        if not re.fullmatch(r"\d+", fields[key]):
            raise CardError(f"Invalid budget: {key}")
        fields[key] = int(fields[key])
    return Card(**fields)
