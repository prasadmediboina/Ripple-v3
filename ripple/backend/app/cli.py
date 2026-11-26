"""RIPPLE CLI. Runs entirely on your machine or in your CI: source code never leaves it.

    python -m app.cli analyze --repo . --base origin/main --head HEAD --format markdown
"""
from __future__ import annotations

import argparse
import json
import sys

from .engine import analyze_snapshots
from .engine.gitutil import file_authors, files_at_ref, merge_base


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ripple")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyze the impact of head relative to base")
    a.add_argument("--repo", default=".")
    a.add_argument("--base", required=True)
    a.add_argument("--head", default="HEAD")
    a.add_argument("--format", choices=["markdown", "json"], default="markdown")
    a.add_argument("--output", help="write to file instead of stdout")
    a.add_argument("--fail-on-gaps", action="store_true", help="exit 2 if changed code is not reachable by any test")
    args = ap.parse_args(argv)

    base_ref = merge_base(args.repo, args.base, args.head)   # PR semantics: diff against merge-base
    report = analyze_snapshots(files_at_ref(args.repo, base_ref), files_at_ref(args.repo, args.head),
                               author_lookup=lambda paths: file_authors(args.repo, args.head, paths))
    text = report.to_markdown() if args.format == "markdown" else json.dumps(report.to_dict(), indent=2)
    if args.output:
        open(args.output, "w").write(text)
    else:
        print(text)
    return 2 if (args.fail_on_gaps and report.coverage_gaps) else 0


if __name__ == "__main__":
    sys.exit(main())
