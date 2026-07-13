#!/usr/bin/env python3
"""Round decimals in a .tex file by significant figures (batch helper)."""

from __future__ import annotations

import argparse
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from latex_hw import LATEX_DIM_RE, NUMBER_RE, read_tex, write_text


def round_sigfigs(value: str, sigfigs: int) -> str:
    try:
        d = Decimal(value)
    except Exception:
        return value
    if d == 0:
        return "0" if sigfigs <= 1 else "0." + "0" * (sigfigs - 1)
    # Use scientific approach
    f = float(d)
    order = math.floor(math.log10(abs(f)))
    decimals = sigfigs - 1 - order
    quant = Decimal("1").scaleb(-decimals) if decimals >= 0 else Decimal(10) ** abs(decimals)
    if decimals >= 0:
        rounded = d.quantize(quant, rounding=ROUND_HALF_UP)
        text = format(rounded, "f")
    else:
        rounded = (d / quant).to_integral_value(rounding=ROUND_HALF_UP) * quant
        text = format(rounded, "f")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite a .tex file rounding every decimal to N significant figures."
    )
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-n", "--sigfigs", type=int, default=3, help="Significant figures")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"error: not found: {src}", file=sys.stderr)
        return 2

    tex = read_tex(src)
    # Protect dimensions
    protected: list[str] = []

    def stash(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return f"@@DIM{len(protected) - 1}@@"

    scrubbed = LATEX_DIM_RE.sub(stash, tex)

    def repl(m: re.Match[str]) -> str:
        token = m.group(1)
        if "." not in token and "e" not in token.lower():
            return token
        return round_sigfigs(token, args.sigfigs)

    rewritten = NUMBER_RE.sub(repl, scrubbed)
    for i, dim in enumerate(protected):
        rewritten = rewritten.replace(f"@@DIM{i}@@", dim)

    out = Path(args.output) if args.output else src.with_name(src.stem + f"_sig{args.sigfigs}.tex")
    write_text(out, rewritten)
    print(f"Rounded decimals to {args.sigfigs} sig figs → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
