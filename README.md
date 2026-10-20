# Predictive Learning

Coursework for Predictive Learning at NTNU.

## Structure

```text
Predictive_Learning/
└── hw1/    Homework 1: Risk Minimization + Model Selection
```

Lecture materials (`Materials/`) are kept local and not tracked.

## Homework 1

| Problems | Topic | Script | Report |
| --- | --- | --- | --- |
| 2.7, 2.8 | kNN classification of US election outcomes from obesity %, k chosen by leave-one-out CV | `solve_classification.py` | `classification_report.md` |
| 2.11, 2.12 | Polynomial regression (trigonometric and algebraic families) with Schwartz-criterion and cross-validated model selection on simulated data | `solve_regression.py` | `regression_report.md` |

- Submission PDF: `hw1/Homework1_61547048S_黃竑喆.pdf`
- Report source: `hw1/report/final_homework1.md` (rebuild the PDF with `uv run --no-project --with markdown python report/build_pdf.py`; requires Google Chrome)
- Diagnostic sklearn reference checks: `sklearn_reference_check.py`, `sklearn_reference_problem_2_8_check.py`

### Setup

```bash
cd hw1
uv venv
uv pip install -r requirements.txt   # or requirements-lock.txt for exact versions
```

### Run

```bash
uv run solve_classification.py   # Problems 2.7 and 2.8
uv run solve_regression.py       # Problems 2.11 and 2.12
```

Outputs (CSV, JSON, and figures) are written to `hw1/results/`.

### Tests and checks

```bash
uv run --with pytest pytest test_classification.py test_regression.py
uv run sklearn_reference_check.py
uv run sklearn_reference_problem_2_8_check.py
```
