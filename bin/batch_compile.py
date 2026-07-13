#!/usr/bin/env python3
"""Batch-compile every .tex file in a folder to PDF (pdflatex)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile all .tex files in a directory.")
    parser.add_argument("-i", "--input-dir", required=True)
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="PDF output directory (default: same as each .tex)",
    )
    parser.add_argument("--engine", default="pdflatex", help="LaTeX engine binary")
    parser.add_argument("--passes", type=int, default=1, help="Compiler passes (default 1)")
    args = parser.parse_args()

    if not shutil.which(args.engine):
        print(f"error: `{args.engine}` not found on PATH", file=sys.stderr)
        return 2

    src = Path(args.input_dir)
    files = sorted(src.glob("*.tex")) if src.is_dir() else ([src] if src.is_file() else [])
    if not files:
        print("No .tex files found.", file=sys.stderr)
        return 1

    out_dir = Path(args.output_dir) if args.output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for tex in files:
        dest = out_dir or tex.parent
        print(f"compiling {tex.name} …")
        success = True
        for _ in range(max(args.passes, 1)):
            proc = subprocess.run(
                [
                    args.engine,
                    "-interaction=nonstopmode",
                    f"-output-directory={dest}",
                    str(tex.resolve()),
                ],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                success = False
                log = dest / (tex.stem + ".log")
                print(f"  FAILED (see {log})", file=sys.stderr)
                break
        if success:
            ok += 1
            print(f"  → {dest / (tex.stem + '.pdf')}")

    print(f"Compiled {ok}/{len(files)} file(s)")
    return 0 if ok == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
