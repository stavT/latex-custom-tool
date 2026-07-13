#!/usr/bin/env python3
"""Generate blank step-by-step solution skeletons for each problem."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import (
    HANDWORKED_STATEMENT,
    read_tex,
    soft_latex,
    split_problems,
    wrap_document,
    write_text,
)


def skeleton_for(index: int, problem: str, steps: int) -> str:
    preview = soft_latex(problem)
    lines = [
        rf"\section*{{Problem {index}}}",
        r"\textbf{Prompt}",
        r"\begin{quote}",
        preview,
        r"\end{quote}",
        "",
        r"\textbf{Work}",
        r"\begin{enumerate}",
    ]
    for s in range(1, steps + 1):
        lines.append(rf"  \item Step {s}: \underline{{\hspace{{0.75\linewidth}}}}")
    lines.extend(
        [
            r"\end{enumerate}",
            "",
            r"\textbf{Final answer}",
            r"\[ \boxed{\phantom{0}} \]",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create blank hand-worked solution skeletons from a problem set."
    )
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("--steps", type=int, default=5, help="Blank steps per problem")
    parser.add_argument("--title", default="Solution Skeleton")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"error: not found: {src}", file=sys.stderr)
        return 2

    problems = split_problems(read_tex(src))
    if not problems:
        print("No problems found.", file=sys.stderr)
        return 1

    parts = [skeleton_for(i, p, args.steps) for i, p in enumerate(problems, start=1)]
    body = "\n".join(parts)
    doc = wrap_document(body, title=args.title, include_handworked=True)
    out = Path(args.output) if args.output else src.with_name(src.stem + "_skeleton.tex")
    write_text(out, doc)
    print(f"Wrote skeleton for {len(problems)} problem(s) → {out}")
    print(HANDWORKED_STATEMENT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
