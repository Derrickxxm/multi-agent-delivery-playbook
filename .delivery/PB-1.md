---
task: PB-1
repo: multi-agent-delivery-playbook (new, local until Owner signs publication)
executor: codex gpt-6.1-sol medium
allowed_paths:
  - playbook/*
  - README.md
  - docs/*
  - pyproject.toml
  - .github/workflows/ci.yml
  - scripts/public_scan.py
  - LICENSE
budget:
  max_files: 16
  max_lines: 1400
---

## Goal
A small, public, synthetic-data repository that shows how one human owner delivers software with AI agents under evidence gates. A recruiter must understand it in 5 minutes: one paragraph, one flowchart, one command.

## Contract (red tests in tests/ are the acceptance criteria; executor must not edit tests/)
Python >= 3.11, stdlib only at runtime; pytest for tests. Package `playbook`:

- `playbook.card.load_card(path) -> Card` parses a Markdown card with YAML-like front matter (simple `key: value` and `  - item` lists, no PyYAML). Fields: `task`, `allowed_paths` (list of glob patterns, fnmatch), `max_files` (int), `max_lines` (int). Missing field -> `CardError`.
- `playbook.gate.evaluate(repo, base, head, evidence) -> Decision` with `Decision.verdict` in {"ALLOW","BLOCK"} and `Decision.codes` (sorted list[str], empty iff ALLOW). Inspect commits `base..head` with git (subprocess). Every commit message carries a trailer line `Role: <architect|executor>`. Rules:
  - CARD_NOT_FIRST: first commit after base must change exactly one file `.delivery/<task>.md` (task from that card).
  - RED_TESTS_NOT_FIRST: the second commit must be by `architect` and change only files under `tests/`.
  - EXECUTOR_TOUCHED_TESTS: any `executor` commit changes a path under `tests/` or `.delivery/`.
  - PATH_VIOLATION: any changed file (excluding the card and tests/) not matching `allowed_paths`.
  - BUDGET_EXCEEDED: files changed (excluding card and tests/) > max_files, or added+deleted lines > max_lines.
  - evidence is a dict with optional keys `review` {"head","p1"}, `ci` {"head","status"}, `signoff` {"head","by"}:
    REVIEW_MISSING / REVIEW_STALE (head != current head) / REVIEW_P1_OPEN (p1 > 0);
    CI_MISSING / CI_STALE / CI_FAILED (status != "pass");
    SIGNOFF_MISSING / SIGNOFF_STALE (head != current head) / SIGNOFF_NOT_OWNER (by != "owner").
  Gate never raises on bad evidence; malformed evidence -> corresponding *_MISSING code.
- `playbook.council.validate(record) -> list[str]` (empty = valid) for a multi-model council record dict:
  `round1` {member -> answer}, `round2_positions` {label -> text}, `devils_advocate` (member), `disagreements` [ {id, ruling} ].
  Errors: NO_DEVILS_ADVOCATE (missing or not a round1 member), NOT_ANONYMIZED (any round1 member name appears in a round2 position text or label), UNRULED (a disagreement without non-empty ruling), TOO_FEW_MEMBERS (<3 members).
- `python -m playbook demo` builds a throwaway git repo in a temp dir, plays one happy path and the attacks below, prints a table (scenario, expected, actual codes) and exits 0 only if every scenario matches expectation. Attacks: executor edits a test; executor touches a file outside scope; budget blown; owner signed an older commit then executor pushed again; review on stale head; CI failed; tests committed after implementation.
- `docs/council-example.md`: a sanitized two-round council (3 members, devil's advocate, anonymized round 2, chair rulings) on a synthetic question, plus `docs/council-example.json` that passes `council.validate`.
- README: first paragraph = what and why; Mermaid flowchart of the 10 steps; "Run it" = `pip install -e . && python -m playbook demo && pytest`; table of blocked attacks; roles table (Owner / architect agent / executor agent); the test count stated must equal the real `pytest` result.
- `.github/workflows/ci.yml`: ubuntu-latest, python 3.11, run demo + pytest.
- `scripts/public_scan.py`: fails (exit 1) if repo text contains IPv4 addresses, `@` emails other than the noreply placeholder and RFC 2606 reserved example domains (example.com/.org/.net, *.example, *.invalid), or any term from a deny-list file passed as argument.

## Not doing
No network, no real data, no secrets, no third-party runtime deps.
