#!/usr/bin/env python3
"""Unified launcher for latex-custom-tool commands."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

COMMANDS = {
    "breakdown": "latex_step_breakdown.py",
    "split": "split_problems.py",
    "organize": "organize_homework.py",
    "handout": "make_handout.py",
    "skeleton": "make_solution_skeleton.py",
    "merge": "merge_homeworks.py",
    "clean": "clean_latex.py",
    "compile": "batch_compile.py",
    "equations": "extract_equations.py",
    "checklist": "homework_checklist.py",
    "sigfigs": "sigfigs_round.py",
}


def main() -> int:
    bin_dir = Path(__file__).resolve().parent
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("latex-hw — math homework automation")
        print()
        print("Usage: python3 bin/latex_hw.py <command> [args...]")
        print()
        print("Commands:")
        for name, script in COMMANDS.items():
            print(f"  {name:<12} → bin/{script}")
        print()
        print("Examples:")
        print("  python3 bin/latex_hw.py breakdown -i examples/sample_problems.tex")
        print("  python3 bin/latex_hw.py split -i examples/sample_problems.tex --wrap")
        print("  python3 bin/latex_hw.py handout -i examples/sample_problems.tex --title 'HW 3'")
        return 0

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Choose from: {', '.join(COMMANDS)}", file=sys.stderr)
        return 2

    script = bin_dir / COMMANDS[cmd]
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
