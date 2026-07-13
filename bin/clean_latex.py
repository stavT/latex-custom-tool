#!/usr/bin/env python3
"""Clean LaTeX homework: strip comments, normalize blank lines, tidy spacing."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import strip_comments, write_text


def clean_tex(tex: str) -> str:
    text = strip_comments(tex)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Space after control words before letters: \itemX -> leave; \item  ok
    text = re.sub(r"\\(item|section|subsection)\*?\s*", lambda m: m.group(0).rstrip() + " ", text)
    return text.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean / normalize LaTeX homework files.")
    parser.add_argument("inputs", nargs="+", help=".tex files")
    parser.add_argument(
        "-i",
        "--inplace",
        action="store_true",
        help="Overwrite files in place",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Write cleaned copies here (ignored with --inplace)",
    )
    args = parser.parse_args()

    for item in args.inputs:
        path = Path(item)
        if not path.is_file():
            print(f"skip missing: {path}", file=sys.stderr)
            continue
        cleaned = clean_tex(path.read_text(encoding="utf-8"))
        if args.inplace:
            path.write_text(cleaned, encoding="utf-8")
            print(f"cleaned {path}")
        else:
            out_dir = Path(args.output_dir) if args.output_dir else path.parent
            out = out_dir / (path.stem + "_clean.tex")
            write_text(out, cleaned)
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
