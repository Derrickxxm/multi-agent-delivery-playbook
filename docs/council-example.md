# Synthetic council: should a Web service add a cache layer?

This invented example contains no customer data or measured production results.
The JSON companion is the machine-checkable record.

## Round 1: independent answers

| Member | Position |
| --- | --- |
| model-a | Measure latency and repeated reads first. |
| model-b | Prototype a short-lived cache for public, read-only responses. |
| model-c | Keep direct reads until benefits justify invalidation complexity. |

The chair assigns model-c as devil's advocate: challenge stale responses,
invalidation failures, memory growth, and the assumption that caching helps.

## Round 2: anonymized positions

The chair removes member attribution before circulating these positions.
Labels do not identify original contributors; the validator checks names only
and cannot establish whether real participants reasoned independently.

| Label | Position |
| --- | --- |
| A | Collect latency, repeated-read, and database-load baselines. |
| B | Trial bounded caching with expiry only if repeated expensive reads justify it. |
| C | Challenge freshness and invalidation failure scenarios. |

## Chair rulings

| Disagreement | Ruling |
| --- | --- |
| D1: implement now or measure first? | Measure first; implementation is not authorized. |
| D2: what would permit a later trial? | Define expiry, memory bounds, and a freshness acceptance check. |

Validate from the repository root:

```python
import json
from pathlib import Path
from playbook.council import validate

assert validate(json.loads(Path("docs/council-example.json").read_text())) == []
```
