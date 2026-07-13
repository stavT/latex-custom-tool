#!/usr/bin/env python3
"""Split a homework .tex into one file per problem."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import read_tex, slugify, split_problems, wrap_document, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Split LaTeX homework into per-problem files.")
    parser.add_argument("-i", "--input", required=True, help="Input .tex file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Output directory (default: <input>_problems/)",
    )
    parser.add_argument(
        "--wrap",
        action="store_true",
        help="Wrap each problem in a full documentclass",
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

    out_dir = Path(args.output_dir) if args.output_dir else src.with_name(src.stem + "_problems")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, problem in enumerate(problems, start=1):
        name = f"{i:02d}_{slugify(problem)}.tex"
        body = (
            wrap_document(f"\\section*{{Problem {i}}}\n\n{problem}\n", title=f"Problem {i}")
            if args.wrap
            else f"% Problem {i}\n{problem}\n"
        )
        write_text(out_dir / name, body)
        print(f"  wrote {out_dir / name}")

    print(f"Split {len(problems)} problem(s) → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
