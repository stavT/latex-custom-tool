#!/usr/bin/env python3
"""Extract equations from homework into a compact review sheet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import extract_equations, read_tex, split_problems, wrap_document, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract math equations into a review sheet.")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("--title", default="Equation Review Sheet")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"error: not found: {src}", file=sys.stderr)
        return 2

    tex = read_tex(src)
    problems = split_problems(tex)
    blocks: list[str] = []

    if problems:
        for i, problem in enumerate(problems, start=1):
            eqs = extract_equations(problem)
            blocks.append(rf"\section*{{Problem {i}}}")
            if not eqs:
                blocks.append(r"\emph{(no explicit math mode found)}")
            else:
                blocks.append(r"\begin{itemize}")
                for eq in eqs:
                    blocks.append(rf"  \item ${eq.strip('$').strip()}$" if eq.count("$") <= 2 else rf"  \item {eq}")
                blocks.append(r"\end{itemize}")
            blocks.append("")
    else:
        eqs = extract_equations(tex)
        blocks.append(r"\begin{itemize}")
        for eq in eqs:
            blocks.append(rf"  \item {eq}")
        blocks.append(r"\end{itemize}")

    out = Path(args.output) if args.output else src.with_name(src.stem + "_equations.tex")
    write_text(out, wrap_document("\n".join(blocks), title=args.title))
    print(f"Wrote equation sheet → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
