from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


DEFAULT_REPO = Path(r"D:\utility_automation_v2")


def run_cmd(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        shell=False,
    )
    return result.stdout.strip()


def copy_to_clipboard(text: str) -> None:
    try:
        subprocess.run(
            ["clip"],
            input=text,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"WARNING: failed to copy to clipboard: {exc}", file=sys.stderr)


def build_payload(repo: Path) -> str:
    branch = run_cmd(["git", "branch", "--show-current"], repo)
    status = run_cmd(["git", "status", "--short"], repo)
    diff_stat = run_cmd(["git", "diff", "--stat"], repo)
    diff = run_cmd(["git", "diff"], repo)

    if not status:
        status = "(clean)"
    if not diff_stat:
        diff_stat = "(no diff)"
    if not diff:
        diff = "(no diff)"

    return f"""Review this git diff for utility_automation_v2.

Context:
- branch: {branch}
- purpose: pre-validation code quality and governance review

Check:
- architecture violations
- determinism violations
- authority expansion
- ledger truth violations
- sqlite authority violations
- mesh/quorum misuse
- hidden shortcuts
- test cheating
- anti-patterns
- frontend mutation surfaces
- GET-only violations
- code smell
- suspicious scope expansion

Git status:
{status}

Git diff stat:
{diff_stat}

Git diff:
{diff}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create AI code review handoff from git diff."
    )
    parser.add_argument(
        "--repo",
        default=str(DEFAULT_REPO),
        help="Repository path",
    )
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="Do not copy payload to clipboard",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"ERROR: repo not found: {repo}", file=sys.stderr)
        return 1

    git_dir = repo / ".git"
    if not git_dir.exists():
        print(f"ERROR: not a git repository: {repo}", file=sys.stderr)
        return 1

    output_dir = repo / "output" / "ai_audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    payload = build_payload(repo)

    out_file = output_dir / f"review-{timestamp}.txt"
    out_file.write_text(payload, encoding="utf-8")

    if not args.no_clipboard:
        copy_to_clipboard(payload)

    print()
    print("AI review handoff created.")
    print(f"Saved: {out_file}")
    if not args.no_clipboard:
        print("Copied to clipboard.")
    print()
    print("Next: paste into ChatGPT for review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())