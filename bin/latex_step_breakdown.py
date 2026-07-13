#!/usr/bin/env python3
"""
Manual LaTeX problem breakdown helper.

Reads a .tex file containing numerical problems, lets you choose rounding
per problem in the terminal, and writes step-by-step worked solutions
in a clean hand-worked style.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import (  # noqa: E402
    HANDWORKED_STATEMENT,
    extract_decimals,
    soft_latex,
    split_problems,
)


@dataclass
class RoundedValue:
    original: str
    rounded: str
    places: int


@dataclass
class Problem:
    index: int
    raw: str
    decimals: list[str] = field(default_factory=list)
    rounded: list[RoundedValue] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    places_note: str = ""

    @property
    def rewritten(self) -> str:
        text = self.raw
        for rv in self.rounded:
            text = text.replace(rv.original, rv.rounded, 1)
        return text

    @property
    def readable_before(self) -> str:
        return soft_latex(self.raw)

    @property
    def readable_after(self) -> str:
        return soft_latex(self.rewritten)


def round_decimal(value: str, places: int) -> str:
    try:
        d = Decimal(value)
    except InvalidOperation:
        return value

    if places < 0:
        quant = Decimal(10) ** abs(places)
        rounded = (d / quant).to_integral_value(rounding=ROUND_HALF_UP) * quant
        return format(rounded, "f")

    quant = Decimal("1").scaleb(-places) if places else Decimal("1")
    rounded = d.quantize(quant, rounding=ROUND_HALF_UP)
    text = format(rounded, "f")
    if places == 0:
        return text.split(".")[0]
    return text


def apply_rounding(
    problem: Problem,
    place_map: list[int | None],
) -> None:
    """
    place_map[i] = decimal places for decimals[i], or None to leave unchanged.
    """
    problem.rounded.clear()
    notes: list[str] = []

    for i, original in enumerate(problem.decimals):
        places = place_map[i] if i < len(place_map) else None
        if places is None:
            notes.append(f"{original} (kept)")
            continue
        rounded = round_decimal(original, places)
        problem.rounded.append(RoundedValue(original, rounded, places))
        notes.append(f"{original} → {rounded} ({places} d.p.)")

    problem.places_note = "; ".join(notes) if notes else "no decimals"
    problem.steps = build_steps(problem)


def build_steps(problem: Problem) -> list[str]:
    steps: list[str] = []
    steps.append("Read the problem and list every decimal value that will be rounded.")

    if not problem.decimals:
        steps.append("No decimal values found — leave exact forms as written.")
        steps.append("Write the final answer using the expressions given in the problem.")
        return steps

    if not problem.rounded:
        steps.append("Leave all decimals unrounded for this problem.")
        steps.append(f"Work with: {problem.readable_before}")
        steps.append("Box / state the final result.")
        return steps

    steps.append(
        f"Apply the chosen rounding for this problem "
        f"({len(problem.rounded)} value(s) modified)."
    )
    for i, rv in enumerate(problem.rounded, start=1):
        steps.append(
            f"Value {i}: {rv.original} → {rv.rounded}  "
            f"(rounded to {rv.places} d.p.)"
        )

    after = problem.readable_after
    steps.append(f"Rewrite with rounded values: {after[:400]}{'…' if len(after) > 400 else ''}")
    steps.append("Carry the rounded values through the remaining arithmetic carefully.")
    steps.append("Box / state the final result using only the rounded figures above.")
    return steps


def prompt_int(prompt: str, default: int | None = None, minimum: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
            if minimum is not None and value < minimum:
                print(f"  Enter an integer ≥ {minimum}.")
                continue
            return value
        except ValueError:
            print("  Enter a whole number.")


def prompt_choice(prompt: str, options: dict[str, str], default: str) -> str:
    keys = "/".join(options)
    while True:
        raw = input(f"{prompt} ({keys}) [{default}]: ").strip().lower() or default
        if raw in options:
            return raw
        print(f"  Choose one of: {keys}")


def parse_index_list(raw: str, count: int) -> list[int]:
    """Parse 'all', '1,3', or '1-3' into 0-based indices."""
    if raw in {"all", "*"}:
        return list(range(count))

    indices: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            start, end = int(left), int(right)
            if start < 1 or end > count or start > end:
                raise ValueError(f"Range {part} out of bounds (1–{count}).")
            indices.update(range(start - 1, end))
        else:
            n = int(part)
            if n < 1 or n > count:
                raise ValueError(f"Index {n} out of bounds (1–{count}).")
            indices.add(n - 1)
    if not indices:
        raise ValueError("No indices selected.")
    return sorted(indices)


def process_file_batch(
    tex_path: Path,
    places: int,
    max_rounds: int | None,
) -> list[Problem]:
    text = tex_path.read_text(encoding="utf-8")
    chunks = split_problems(text)
    problems: list[Problem] = []

    for i, chunk in enumerate(chunks, start=1):
        problem = Problem(index=i, raw=chunk, decimals=extract_decimals(chunk))
        targets = problem.decimals
        if max_rounds is not None:
            place_map: list[int | None] = [
                places if j < max_rounds else None for j in range(len(targets))
            ]
        else:
            place_map = [places] * len(targets)
        apply_rounding(problem, place_map)
        problems.append(problem)

    return problems


def process_file_interactive(
    tex_path: Path,
    default_places: int,
) -> list[Problem]:
    text = tex_path.read_text(encoding="utf-8")
    chunks = split_problems(text)
    if not chunks:
        return []

    total = len(chunks)
    problems: list[Problem] = []
    print()
    print(f"Found {total} problem(s) in {tex_path.name}")
    print(HANDWORKED_STATEMENT)

    for i, chunk in enumerate(chunks, start=1):
        problem = Problem(index=i, raw=chunk, decimals=extract_decimals(chunk))
        # Fix the transient "of …" label
        print()
        print("=" * 60)
        print(f"  PROBLEM {i} of {total}")
        print("=" * 60)
        print("BEFORE:")
        print(f"  {problem.readable_before}")
        print()
        if problem.decimals:
            print("Decimals found:")
            for j, val in enumerate(problem.decimals, start=1):
                print(f"  [{j}] {val}")
        else:
            print("  (no decimal numbers found)")

        if not problem.decimals:
            apply_rounding(problem, [])
            print("AFTER:  (unchanged — no decimals)")
            problems.append(problem)
            continue

        print()
        print("Rounding options for this problem:")
        print("  a  = round ALL decimals to the same # of places")
        print("  s  = SELECT which decimals to round (same places)")
        print("  e  = set places for EACH decimal individually")
        print("  k  = keep all decimals (no rounding)")
        print("  q  = quit script")

        mode = prompt_choice(
            "Choice",
            {"a": "all", "s": "select", "e": "each", "k": "keep", "q": "quit"},
            "a",
        )
        if mode == "q":
            print("Stopped early — writing problems configured so far.")
            break

        place_map: list[int | None] = [None] * len(problem.decimals)

        if mode == "k":
            apply_rounding(problem, place_map)
        elif mode == "a":
            places = prompt_int("Decimal places for all", default=default_places, minimum=0)
            place_map = [places] * len(problem.decimals)
            apply_rounding(problem, place_map)
        elif mode == "s":
            places = prompt_int("Decimal places for selected", default=default_places, minimum=0)
            while True:
                raw = input(
                    "Which numbers to round? (e.g. 1,3 or 1-3 or all) [all]: "
                ).strip().lower() or "all"
                try:
                    indices = parse_index_list(raw, len(problem.decimals))
                    break
                except ValueError as exc:
                    print(f"  {exc}")
            for idx in indices:
                place_map[idx] = places
            apply_rounding(problem, place_map)
        else:
            print("Enter places for each value (blank = default, 'k' = keep):")
            for j, val in enumerate(problem.decimals):
                raw = input(f"  [{j + 1}] {val} → places [{default_places}]: ").strip()
                if raw.lower() in {"", "d"}:
                    place_map[j] = default_places
                elif raw.lower() in {"k", "keep", "-"}:
                    place_map[j] = None
                else:
                    try:
                        p = int(raw)
                        place_map[j] = max(p, 0)
                    except ValueError:
                        print(f"    Invalid; keeping {val} unrounded.")
                        place_map[j] = None
            apply_rounding(problem, place_map)

        print()
        print("AFTER:")
        print(f"  {problem.readable_after}")
        if problem.rounded:
            print("Rounded:")
            for rv in problem.rounded:
                print(f"  {rv.original} → {rv.rounded} ({rv.places} d.p.)")
        problems.append(problem)

    return problems


def render_markdown(problems: list[Problem]) -> str:
    lines: list[str] = [
        "# LaTeX Problem Breakdown",
        "",
        HANDWORKED_STATEMENT,
        "",
    ]

    for p in problems:
        lines.append(f"## Problem {p.index}")
        lines.append("")
        lines.append("### Before")
        lines.append("")
        lines.append("```latex")
        lines.append(p.raw.strip()[:2000])
        lines.append("```")
        lines.append("")
        lines.append(f"_Readable:_ {p.readable_before}")
        lines.append("")
        lines.append("### After")
        lines.append("")
        lines.append("```latex")
        lines.append(p.rewritten.strip()[:2000])
        lines.append("```")
        lines.append("")
        lines.append(f"_Readable:_ {p.readable_after}")
        lines.append("")

        if p.rounded:
            lines.append("**Rounded values**")
            lines.append("")
            for rv in p.rounded:
                lines.append(f"- `{rv.original}` → `{rv.rounded}` ({rv.places} d.p.)")
            lines.append("")
        elif p.decimals:
            lines.append("_No values were rounded for this problem._")
            lines.append("")

        if p.places_note:
            lines.append(f"_Choices:_ {p.places_note}")
            lines.append("")

        lines.append("**Steps**")
        lines.append("")
        for n, step in enumerate(p.steps, start=1):
            lines.append(f"{n}. {step}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(HANDWORKED_STATEMENT)
    lines.append("")
    return "\n".join(lines)


def render_latex(problems: list[Problem]) -> str:
    lines: list[str] = [
        r"\documentclass{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{amsmath,amssymb}",
        r"\begin{document}",
        "",
        r"\begin{center}",
        r"{\Large Worked Solutions (After Rounding)}\\[0.75em]",
        r"\end{center}",
        "",
        # Required statement — always embedded in the compiled document
        r"\begin{center}",
        r"\fbox{\parbox{0.92\textwidth}{\centering\textit{"
        + HANDWORKED_STATEMENT
        + r"}}}",
        r"\end{center}",
        "",
        r"\vspace{1em}",
        "",
    ]

    for p in problems:
        lines.append(rf"\section*{{Problem {p.index}}}")
        lines.append(r"\textbf{Before}")
        lines.append(r"\begin{verbatim}")
        lines.append(p.raw.strip()[:1500].replace("\\end{verbatim}", "[end-verbatim]"))
        lines.append(r"\end{verbatim}")
        lines.append(r"\textbf{After}")
        lines.append(r"\begin{verbatim}")
        lines.append(p.rewritten.strip()[:1500].replace("\\end{verbatim}", "[end-verbatim]"))
        lines.append(r"\end{verbatim}")

        if p.rounded:
            lines.append(r"\textbf{Rounded values}")
            lines.append(r"\begin{itemize}")
            for rv in p.rounded:
                lines.append(
                    rf"  \item ${rv.original}$ $\rightarrow$ ${rv.rounded}$ "
                    rf"({rv.places} d.p.)"
                )
            lines.append(r"\end{itemize}")

        lines.append(r"\textbf{Steps}")
        lines.append(r"\begin{enumerate}")
        for step in p.steps:
            escaped = (
                step.replace("\\", r"\textbackslash{}")
                .replace("&", r"\&")
                .replace("%", r"\%")
                .replace("#", r"\#")
                .replace("_", r"\_")
                .replace("{", r"\{")
                .replace("}", r"\}")
            )
            lines.append(rf"  \item {escaped}")
        lines.append(r"\end{enumerate}")
        lines.append("")

    lines.append(r"\begin{quote}")
    lines.append(HANDWORKED_STATEMENT)
    lines.append(r"\end{quote}")
    lines.append(r"\end{document}")
    lines.append("")
    return "\n".join(lines)


def resolve_io(args: argparse.Namespace) -> tuple[Path, Path, str, int]:
    if args.input:
        tex_path = Path(args.input)
    else:
        tex_path = Path(input("Path to LaTeX (.tex) file: ").strip())
    if not tex_path.is_file():
        raise SystemExit(f"File not found: {tex_path}")

    default_places = (
        args.places
        if args.places is not None
        else (2 if args.yes else prompt_int("Default decimal places", default=2, minimum=0))
    )

    fmt = args.format
    if not fmt:
        if args.yes:
            fmt = "md"
        else:
            fmt = input("Output format — md or tex [md]: ").strip().lower() or "md"
    if fmt not in {"md", "tex"}:
        raise SystemExit("format must be 'md' or 'tex'")

    if args.output:
        out = Path(args.output)
    elif args.yes:
        out = tex_path.with_name(tex_path.stem + f"_steps.{fmt}")
    else:
        default_out = tex_path.with_name(tex_path.stem + f"_steps.{fmt}")
        typed = input(f"Output path [{default_out}]: ").strip()
        out = Path(typed) if typed else default_out

    return tex_path, out, fmt, default_places


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Break down LaTeX problem files: choose rounding per problem "
            "in the terminal and write step-by-step hand-worked solutions."
        )
    )
    parser.add_argument("-i", "--input", help="Input .tex file")
    parser.add_argument(
        "-p",
        "--places",
        type=int,
        help="Default decimal places (used as the prompt default / batch mode)",
    )
    parser.add_argument(
        "-n",
        "--max-rounds",
        type=int,
        dest="max_rounds",
        help="Batch mode only: max decimals to round per problem",
    )
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=["md", "tex"], help="Output format")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Non-interactive batch mode (same rounding for every problem)",
    )
    parser.add_argument(
        "--per-problem",
        action="store_true",
        dest="per_problem",
        help="Force per-problem terminal prompts (default when not using -y)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.yes and not args.input:
        print("error: --yes requires --input", file=sys.stderr)
        return 2

    tex_path, out, fmt, default_places = resolve_io(args)

    if args.yes and not args.per_problem:
        problems = process_file_batch(tex_path, default_places, args.max_rounds)
    else:
        problems = process_file_interactive(tex_path, default_places)

    if not problems:
        print("No problems found in the file.", file=sys.stderr)
        return 1

    body = render_markdown(problems) if fmt == "md" else render_latex(problems)
    out.write_text(body, encoding="utf-8")

    print()
    print(f"Wrote {len(problems)} problem(s) → {out}")
    print(HANDWORKED_STATEMENT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
