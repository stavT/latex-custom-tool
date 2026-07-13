#!/usr/bin/env python3
"""Merge multiple problem .tex snippets/files into one homework document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import read_tex, split_problems, wrap_document, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge LaTeX problem files into one handout.")
    parser.add_argument("inputs", nargs="+", help="Input .tex files or directories")
    parser.add_argument("-o", "--output", required=True, help="Output .tex path")
    parser.add_argument("--title", default="Combined Homework")
    parser.add_argument(
        "--solutions",
        action="store_true",
        help="Include hand-worked statement banner",
    )
    args = parser.parse_args()

    paths: list[Path] = []
    for item in args.inputs:
        p = Path(item)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.tex")))
        elif p.is_file():
            paths.append(p)
        else:
            print(f"warning: skip missing {p}", file=sys.stderr)

    if not paths:
        print("No input files.", file=sys.stderr)
        return 1

    all_problems: list[str] = []
    for path in paths:
        chunks = split_problems(read_tex(path))
        if chunks:
            all_problems.extend(chunks)
        else:
            all_problems.append(read_tex(path).strip())

    items = "\n".join(f"  \\item {p.strip()}" for p in all_problems)
    body = "\n".join(
        [
            r"\begin{enumerate}[leftmargin=*]",
            items,
            r"\end{enumerate}",
            "",
        ]
    )
    doc = wrap_document(body, title=args.title, include_handworked=args.solutions)
    write_text(Path(args.output), doc)
    print(f"Merged {len(paths)} file(s) / {len(all_problems)} problem(s) → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
