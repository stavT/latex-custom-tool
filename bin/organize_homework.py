#!/usr/bin/env python3
"""Organize homework .tex files into a clean folder tree by course/week/topic."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import read_tex, soft_latex, split_problems, write_text


META_RE = re.compile(
    r"(?im)^\s*%\s*(course|week|chapter|section|due|topic)\s*[:=]\s*(.+?)\s*$"
)


def parse_meta(tex: str) -> dict[str, str]:
    meta = {"course": "general", "week": "unsorted", "topic": "misc"}
    for m in META_RE.finditer(tex):
        meta[m.group(1).lower()] = re.sub(r"[^\w\-]+", "-", m.group(2).strip()).strip("-").lower() or meta.get(
            m.group(1).lower(), "misc"
        )
    # Fallbacks from filename patterns like HW03_calc_week2.tex
    return meta


def infer_from_name(path: Path, meta: dict[str, str]) -> dict[str, str]:
    name = path.stem.lower()
    week = re.search(r"week[_-]?(\d+)", name)
    hw = re.search(r"hw[_-]?(\d+)", name)
    ch = re.search(r"ch(?:apter)?[_-]?(\d+)", name)
    if week:
        meta["week"] = f"week-{int(week.group(1)):02d}"
    elif hw:
        meta["week"] = f"hw-{int(hw.group(1)):02d}"
    if ch:
        meta["topic"] = f"chapter-{int(ch.group(1)):02d}"
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Organize .tex homeworks into course/week/topic folders."
    )
    parser.add_argument("-i", "--input-dir", required=True, help="Folder of .tex files")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="organized_homework",
        help="Destination root (default: organized_homework)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy instead of moving files",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Also write INDEX.md summarizing every file",
    )
    args = parser.parse_args()

    src_dir = Path(args.input_dir)
    out_root = Path(args.output_dir)
    if not src_dir.is_dir():
        print(f"error: not a directory: {src_dir}", file=sys.stderr)
        return 2

    files = sorted(src_dir.rglob("*.tex"))
    if not files:
        print("No .tex files found.", file=sys.stderr)
        return 1

    index_rows: list[str] = ["# Homework index", ""]
    for path in files:
        tex = read_tex(path)
        meta = infer_from_name(path, parse_meta(tex))
        dest_dir = out_root / meta["course"] / meta["week"] / meta["topic"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if args.copy:
            shutil.copy2(path, dest)
        else:
            shutil.move(str(path), str(dest))
        n_probs = len(split_problems(tex))
        preview = soft_latex(tex)[:80]
        index_rows.append(
            f"- `{dest.relative_to(out_root)}` — {n_probs} problem(s) — {preview}…"
        )
        print(f"  {path.name} → {dest}")

    if args.index:
        write_text(out_root / "INDEX.md", "\n".join(index_rows) + "\n")
        print(f"Wrote {out_root / 'INDEX.md'}")

    print(f"Organized {len(files)} file(s) → {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
