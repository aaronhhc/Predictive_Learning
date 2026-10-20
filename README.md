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
| 2.11, 2.12 | Polynomial regression (trigonometric and algebraic families) with cross-validated model selection on simulated data | `solve_regression.py` | `regression_report.md` |
| Extra | Odd-k sensitivity analysis for kNN | | `sensitivity_report.md` |

The combined write-up is in `hw1/report/final_homework1.md`, and the submitted PDF is in `hw1/`.

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

### Notes

- The original ten observations from Example 2.6 were unavailable, so the regression problems use a reproducible simulated realization (seed `20261006`), saved in `hw1/results/example_2_6_simulated.csv`.
- Requires scikit-learn 1.9.1 and matplotlib 3.10.8 (see `requirements.txt`).
