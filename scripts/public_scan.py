"""Scan UTF-8 repository text for publication blockers."""

import argparse
import ipaddress
import os
from pathlib import Path
import re


IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
RESERVED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}


def is_example_email(address):
    domain = address.rsplit("@", 1)[1].casefold()
    return domain in RESERVED_EMAIL_DOMAINS or domain.endswith((".example", ".invalid"))


def walk_error(error):
    raise error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deny_list", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("--root must be a directory")
    terms = [line.strip().casefold() for line in args.deny_list.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    findings = []
    for directory, folders, files in os.walk(root, followlinks=False, onerror=walk_error):
        folders[:] = sorted(folder for folder in folders
                            if folder not in {".git", ".venv", "__pycache__", ".pytest_cache"}
                            and not (Path(directory) / folder).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.parent == root and name in {"codex.log", "codex.pid"}:
                continue
            if path.is_symlink() or path.resolve() == args.deny_list.resolve():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # Binary assets are outside this text-only scanner.
            for number, line in enumerate(text.splitlines(), 1):
                kinds = set()
                for match in IPV4.finditer(line):
                    try:
                        ipaddress.IPv4Address(match.group())
                    except ipaddress.AddressValueError:
                        continue
                    kinds.add("IPv4")
                if any(not is_example_email(match.group()) for match in EMAIL.finditer(line)):
                    kinds.add("email")
                if any(term in line.casefold() for term in terms):
                    kinds.add("deny-list")
                if kinds:
                    findings.append(f"{path.relative_to(root)}:{number}: {', '.join(sorted(kinds))}")
    for finding in findings:
        print(finding)
    print(f"Public scan: {'BLOCK' if findings else 'PASS'} ({len(findings)} matching lines)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
