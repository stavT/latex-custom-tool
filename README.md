# latex-custom-tool

Python CLI toolkit that organizes math-style LaTeX homework quickly: split problems, round decimals, build handouts, generate solution skeletons, checklists, equation review sheets, and batch-compile PDFs. Solution outputs are stamped with a short hand-worked / rounding note so every writeup stays consistent.

## Requirements

- Python 3.10+
- Optional: `pdflatex` (or another LaTeX engine) for PDF compilation

No third-party Python packages required.

## Quick start

```bash
git clone https://github.com/stavT/latex-custom-tool.git
cd latex-custom-tool

# See all commands
python3 bin/latex_hw.py

# Interactive per-problem rounding + step breakdown
python3 bin/latex_hw.py breakdown -i examples/sample_problems.tex

# Non-interactive batch (2 decimal places → Markdown)
python3 bin/latex_hw.py breakdown -i examples/sample_problems.tex -p 2 -f md -o output/steps.md -y

# Same, but write a compilable .tex solution set
python3 bin/latex_hw.py breakdown -i examples/sample_problems.tex -p 2 -f tex -o output/steps.tex -y
pdflatex -output-directory output output/steps.tex
```

## Commands

Use the unified launcher or call scripts under `bin/` directly.

| Command | Script | What it does |
|---------|--------|--------------|
| `breakdown` | `latex_step_breakdown.py` | Split problems, choose rounding in the terminal (or batch), write step-by-step before/after work |
| `split` | `split_problems.py` | One `.tex` file per problem |
| `organize` | `organize_homework.py` | Sort files into `course/week/topic/` using `% course:` metadata or filename hints |
| `handout` | `make_handout.py` | Clean titled homework handout |
| `skeleton` | `make_solution_skeleton.py` | Blank hand-worked solution pages |
| `merge` | `merge_homeworks.py` | Combine many problem files into one assignment |
| `clean` | `clean_latex.py` | Strip comments, normalize blank lines |
| `compile` | `batch_compile.py` | Compile every `.tex` in a folder to PDF |
| `equations` | `extract_equations.py` | Pull math into a review sheet |
| `checklist` | `homework_checklist.py` | Markdown/LaTeX progress checklist |
| `sigfigs` | `sigfigs_round.py` | Rewrite decimals to N significant figures |

### `breakdown` — rounding + steps

**Interactive (recommended)** — for each problem you pick:

- `a` round **all** decimals to the same places  
- `s` **select** which decimals to round  
- `e` set places for **each** decimal  
- `k` keep unrounded  
- `q` quit and write what you finished  

```bash
python3 bin/latex_step_breakdown.py -i examples/sample_problems.tex
```

**Batch mode:**

```bash
python3 bin/latex_step_breakdown.py \
  -i examples/sample_problems.tex \
  -p 2 \
  -n 2 \
  -f tex \
  -o output/after.tex \
  -y
```

| Flag | Meaning |
|------|---------|
| `-i` | Input `.tex` |
| `-p` | Default decimal places |
| `-n` | Max decimals to round per problem (batch) |
| `-f md\|tex` | Output format |
| `-o` | Output path |
| `-y` | Non-interactive |

### `split` — one file per problem

```bash
python3 bin/latex_hw.py split -i examples/sample_problems.tex -o output/problems --wrap
```

### `organize` — folder tree

Add metadata comments at the top of a `.tex` file:

```latex
% course: calculus-1
% week: 03
% topic: derivatives
% due: 2026-07-20
```

```bash
python3 bin/latex_hw.py organize -i ./inbox -o ./organized --copy --index
```

Creates paths like `organized/calculus-1/week-03/derivatives/…` plus `INDEX.md`.

### `handout` — clean assignment sheet

```bash
python3 bin/latex_hw.py handout \
  -i examples/sample_problems.tex \
  -o output/hw03.tex \
  --title "Homework 3" \
  --course "Calculus I" \
  --name "Your Name" \
  --due 2026-07-20
```

Add `--solutions` if you want the usual hand-worked / rounding footer on the packet.

### `skeleton` — blank step pages

```bash
python3 bin/latex_hw.py skeleton -i examples/sample_problems.tex --steps 6 -o output/skeleton.tex
```

### `merge` — combine problem banks

```bash
python3 bin/latex_hw.py merge examples/sample_problems.tex output/problems -o output/combined.tex --title "Midterm Review"
```

### `clean` — tidy source

```bash
python3 bin/latex_hw.py clean examples/sample_problems.tex -o output
# or overwrite:
python3 bin/latex_hw.py clean path/to/messy.tex --inplace
```

### `compile` — batch PDFs

```bash
python3 bin/latex_hw.py compile -i output -o output --passes 1
```

### `equations` — review sheet

```bash
python3 bin/latex_hw.py equations -i examples/sample_problems.tex -o output/equations.tex
```

### `checklist` — track progress

```bash
python3 bin/latex_hw.py checklist -i examples/sample_problems.tex -f md -o output/todo.md
```

### `sigfigs` — significant figures

```bash
python3 bin/latex_hw.py sigfigs -i examples/sample_problems.tex -n 3 -o output/sig3.tex
```

## Suggested workflow

1. Drop raw homework `.tex` into an inbox folder  
2. `organize` → sorted tree  
3. `split` or `handout` → working copies  
4. `breakdown` → rounded values + step-by-step writeup  
5. `skeleton` if you want blank work pages first  
6. `compile` → PDFs  

## Project layout

```
latex-custom-tool/
├── bin/                 # CLI scripts
├── latex_hw/            # shared parsing helpers
├── examples/            # sample homework
├── output/              # your generated files (gitignored)
└── README.md
```

## License

MIT
