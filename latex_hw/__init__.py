"""Shared helpers for LaTeX math-homework automation."""

from __future__ import annotations

import re
from pathlib import Path

HANDWORKED_STATEMENT = (
    "Step-by-step work written in a clean, hand-worked style. "
    "Values are rounded exactly as requested in each problem."
)

END_ENV_RE = re.compile(r"\\end\{[^}]+\}", re.IGNORECASE)

PROBLEM_SPLIT_RE = re.compile(
    r"(?:"
    r"\\(?:begin\{(?:enumerate|itemize|problems?|exercises?)\}|"
    r"item(?:\[[^\]]*\])?|"
    r"(?:sub)*section\*?\{[^}]*\}|"
    r"textbf\{(?:Problem|Exercise|Question)\s*[^}]*\}|"
    r"(?:Problem|Exercise|Question)\s*\d+[.:]?)"
    r")",
    re.IGNORECASE,
)

NUMBERED_LINE_RE = re.compile(
    r"(?m)^(?:\s*(?:\d+[.)]|[A-Za-z][.)]|\([a-zA-Z0-9]+\))\s+)"
)

LATEX_DIM_RE = re.compile(
    r"(?<![A-Za-z\\])"
    r"([+-]?(?:\d+\.\d+|\.\d+|\d+))"
    r"(?:em|ex|pt|bp|dd|pc|in|cm|mm|mu|sp)\b",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(
    r"(?<![A-Za-z\\])"
    r"(?<!\d)"
    r"([+-]?(?:\d+\.\d+|\.\d+|\d+)(?:[eE][+-]?\d+)?)"
    r"(?!\d)"
    r"(?![a-zA-Z])"
)

EQUATION_RE = re.compile(
    r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)|"
    r"\\begin\{(?:equation|align|gather|multline)\*?\}.*?\\end\{(?:equation|align|gather|multline)\*?\})",
    re.DOTALL,
)


def strip_comments(tex: str) -> str:
    return re.sub(r"(?<!\\)%.*?$", "", tex, flags=re.MULTILINE)


def document_body(tex: str) -> str:
    cleaned = strip_comments(tex)
    begin_doc = re.search(r"\\begin\{document\}", cleaned, re.IGNORECASE)
    end_doc = re.search(r"\\end\{document\}", cleaned, re.IGNORECASE)
    if not begin_doc:
        return cleaned
    start = begin_doc.end()
    end = end_doc.start() if end_doc else len(cleaned)
    return cleaned[start:end]


def is_formatting_chunk(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    command_chars = len(re.findall(r"\\[a-zA-Z]+|[{}]", stripped))
    letters = len(re.findall(r"[A-Za-z]", stripped))
    if letters < 20 and command_chars >= 3:
        return True
    if re.search(
        r"Original Problems|Before Rounding|After Rounding|Worked Solutions|"
        r"Sample Numerical Homework|\\begin\{center\}",
        stripped,
        re.I,
    ):
        return True
    # Title-only blocks: Large/huge centered headings without enumerate-like prompts
    if re.search(r"\\(?:Large|LARGE|huge|Huge)\b", stripped) and not extract_decimals(stripped):
        if len(soft_latex(stripped)) < 120:
            return True
    return False


def split_problems(tex: str) -> list[str]:
    body = document_body(tex)

    # Prefer enumerate/itemize item bodies when present
    enum = re.search(
        r"\\begin\{(?:enumerate|itemize|problems?|exercises?)\}(.*)\\end\{(?:enumerate|itemize|problems?|exercises?)\}",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    if enum:
        items = re.split(r"\\item(?:\[[^\]]*\])?", enum.group(1))
        item_chunks = [END_ENV_RE.sub("", p).strip() for p in items if p and p.strip()]
        item_chunks = [c for c in item_chunks if c and not is_formatting_chunk(c)]
        if len(item_chunks) >= 1:
            return item_chunks

    parts = PROBLEM_SPLIT_RE.split(body)
    chunks = [p.strip() for p in parts if p and p.strip()]
    meaningful: list[str] = []
    for c in chunks:
        stripped = END_ENV_RE.sub("", c).strip()
        if not stripped or is_formatting_chunk(stripped):
            continue
        if extract_decimals(stripped) or len(stripped) > 40:
            meaningful.append(stripped)

    if len(meaningful) >= 2:
        return meaningful

    numbered = NUMBERED_LINE_RE.split(body)
    numbered = [END_ENV_RE.sub("", p).strip() for p in numbered if p and p.strip()]
    numbered = [p for p in numbered if p and not is_formatting_chunk(p)]
    if len(numbered) >= 2:
        return numbered

    paras = [END_ENV_RE.sub("", p).strip() for p in re.split(r"\n\s*\n+", body) if p.strip()]
    with_nums = [p for p in paras if (extract_decimals(p) or len(p) > 40) and not is_formatting_chunk(p)]
    return with_nums if with_nums else ([body.strip()] if body.strip() else [])


def extract_decimals(text: str) -> list[str]:
    scrubbed = LATEX_DIM_RE.sub(" ", text)
    found: list[str] = []
    for match in NUMBER_RE.finditer(scrubbed):
        token = match.group(1)
        if "." in token or "e" in token.lower():
            found.append(token)
    return found


def extract_equations(text: str) -> list[str]:
    return [m.group(0).strip() for m in EQUATION_RE.finditer(text)]


def soft_latex(text: str) -> str:
    readable = END_ENV_RE.sub("", text)
    readable = re.sub(r"\\(?:textbf|textit|mathrm|mathbf|text)\{([^}]*)\}", r"\1", readable)
    readable = re.sub(r"\\(?:frac|dfrac|tfrac)\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", readable)
    readable = re.sub(r"\\(?:left|right|big|Big)", "", readable)
    readable = re.sub(r"\$+", "", readable)
    readable = re.sub(r"\s+", " ", readable).strip()
    return readable


def wrap_document(
    body: str,
    title: str | None = None,
    include_handworked: bool = False,
) -> str:
    lines = [
        r"\documentclass{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{amsmath,amssymb,amsthm}",
        r"\usepackage{enumitem}",
        r"\begin{document}",
        "",
    ]
    if title:
        lines.extend(
            [
                r"\begin{center}",
                rf"{{\Large {title}}}\\[0.5em]",
                r"\end{center}",
                "",
            ]
        )
    if include_handworked:
        lines.extend(
            [
                r"\begin{center}",
                r"\fbox{\parbox{0.92\textwidth}{\centering\textit{"
                + HANDWORKED_STATEMENT
                + r"}}}",
                r"\end{center}",
                r"\vspace{1em}",
                "",
            ]
        )
    lines.append(body.rstrip())
    lines.append("")
    if include_handworked:
        lines.extend(
            [
                r"\vspace{1em}",
                r"\begin{center}",
                r"\textit{" + HANDWORKED_STATEMENT + r"}",
                r"\end{center}",
                "",
            ]
        )
    lines.append(r"\end{document}")
    lines.append("")
    return "\n".join(lines)


def slugify(text: str, max_len: int = 40) -> str:
    soft = soft_latex(text)
    soft = re.sub(r"[^A-Za-z0-9]+", "-", soft).strip("-").lower()
    return (soft[:max_len] or "problem").rstrip("-")


def read_tex(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: Path | str, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
