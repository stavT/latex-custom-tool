#!/usr/bin/env python3
"""Build a clean titled homework handout from a problem .tex file."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import HANDWORKED_STATEMENT, read_tex, split_problems, wrap_document, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean LaTeX homework handout.")
    parser.add_argument("-i", "--input", required=True, help="Input .tex with problems")
    parser.add_argument("-o", "--output", help="Output .tex path")
    parser.add_argument("--title", default="Homework", help="Document title")
    parser.add_argument("--course", default="", help="Course name line")
    parser.add_argument("--name", default="", help="Student name line")
    parser.add_argument("--due", default="", help="Due date (default: today)")
    parser.add_argument(
        "--solutions",
        action="store_true",
        help="Include the hand-worked statement banner (for solution sets)",
    )
    args = parser.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"error: not found: {src}", file=sys.stderr)
        return 2

    problems = split_problems(read_tex(src))
    if not problems:
        print("No problems found.", file=sys.stderr)
        return 1

    due = args.due or date.today().isoformat()
    header_bits = [p for p in [args.course, args.name, f"Due: {due}"] if p]
    header = r"\\".join(header_bits)

    items = "\n".join(f"  \\item {p.strip()}" for p in problems)
    body = "\n".join(
        [
            r"\begin{center}",
            rf"{{\Large {args.title}}}\\[0.4em]",
            header,
            r"\end{center}",
            "",
            r"\begin{enumerate}[leftmargin=*]",
            items,
            r"\end{enumerate}",
            "",
        ]
    )

    # wrap_document already adds title optionally; we embedded title in body
    doc = wrap_document(body, title=None, include_handworked=args.solutions)
    # If solutions flag, statement is included; also print reminder
    out = Path(args.output) if args.output else src.with_name(src.stem + "_handout.tex")
    write_text(out, doc)
    print(f"Wrote handout with {len(problems)} problem(s) → {out}")
    if args.solutions:
        print(HANDWORKED_STATEMENT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
