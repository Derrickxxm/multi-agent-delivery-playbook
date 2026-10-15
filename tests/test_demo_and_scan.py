import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_demo_runs_and_passes():
    out = subprocess.run([sys.executable, "-m", "playbook", "demo"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    for name in ("happy", "executor edits test", "out of scope", "budget", "stale signoff", "stale review",
                 "ci failed", "tests after implementation"):
        assert name in out.stdout


def test_public_scan_clean_repo(tmp_path):
    deny = tmp_path / "deny.txt"
    deny.write_text("internal-host-name\n")
    out = subprocess.run([sys.executable, "scripts/public_scan.py", str(deny)], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_public_scan_catches(tmp_path):
    bad = tmp_path / "repo"
    (bad / "docs").mkdir(parents=True)
    (bad / "docs" / "x.md").write_text("server at 10.1.2.3 and alice@corp.example and internal-host-name\n")
    deny = tmp_path / "deny.txt"
    deny.write_text("internal-host-name\n")
    out = subprocess.run([sys.executable, str(ROOT / "scripts/public_scan.py"), str(deny), "--root", str(bad)],
                         capture_output=True, text=True)
    assert out.returncode == 1
