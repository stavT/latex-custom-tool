#!/usr/bin/env python3
"""Generate a markdown/LaTeX checklist from homework problems."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import extract_decimals, read_tex, soft_latex, split_problems, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a homework progress checklist.")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument(
        "-f",
        "--format",
        choices=["md", "tex"],
        default="md",
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

    out = Path(args.output) if args.output else src.with_name(src.stem + f"_checklist.{args.format}")

    if args.format == "md":
        lines = [f"# Checklist — {src.name}", "", f"Total problems: {len(problems)}", ""]
        for i, p in enumerate(problems, start=1):
            preview = soft_latex(p)[:100]
            decimals = extract_decimals(p)
            extra = f" _(decimals: {', '.join(decimals)})_" if decimals else ""
            lines.append(f"- [ ] **Problem {i}** — {preview}{extra}")
        lines.append("")
        write_text(out, "\n".join(lines))
    else:
        items = []
        for i, p in enumerate(problems, start=1):
            preview = soft_latex(p)[:100].replace("&", r"\&")
            items.append(rf"  \item[$\square$] Problem {i}: {preview}")
        body = "\n".join(
            [
                r"\begin{itemize}",
                *items,
                r"\end{itemize}",
            ]
        )
        from latex_hw import wrap_document

        write_text(out, wrap_document(body, title=f"Checklist — {src.stem}"))

    print(f"Wrote checklist ({len(problems)} items) → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
