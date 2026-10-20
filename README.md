# Predictive Learning

Coursework for Predictive Learning at NTNU.

## Structure

```
Predictive_Learning/
└── hw1/    Homework 1: Risk Minimization + Model Selection
```

Lecture materials (`Materials/`) are kept local and not tracked.

## Homework 1

| Problems | Topic | Script | Report |
|---|---|---|---|
| 2.7, 2.8 | kNN classification of US election outcomes from obesity %, k chosen by leave-one-out CV | `solve_classification.py` | `classification_report.md` |
| 2.11, 2.12 | Polynomial regression (trigonometric and algebraic families) with cross-validated model selection on simulated data | `solve_regression.py` | `regression_report.md` |
| Extra | Odd-k sensitivity analysis for kNN | | `sensitivity_report.md` |

The combined write-up is in `hw1/report/final_homework1.md`, and the submitted PDF is in `hw1/`.

### Setup

```bash
cd hw1
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or requirements-lock.txt for exact versions
```

### Run

```bash
python solve_classification.py   # Problems 2.7 and 2.8
python solve_regression.py       # Problems 2.11 and 2.12
```

Outputs (CSV, JSON, and figures) are written to `hw1/results/`.

### Tests and checks

```bash
python -m pytest test_classification.py test_regression.py
python sklearn_reference_check.py
python sklearn_reference_problem_2_8_check.py
```

### Key results (kNN, 51 states and DC)

| Problem | Train → test | Selected k | LOOCV error | Test error |
|---|---|---:|---:|---:|
| 2.7 | 2004 → 2000 | 7 | 27.45% | 52.94% |
| 2.8 | 2000 → 2004 | 16 | 37.25% | 37.25% |

Ties in minimum LOOCV error are broken by choosing the smallest k.

### Notes

- The original ten observations from Example 2.6 were unavailable, so the regression problems use a reproducible simulated realization (seed `20261006`), saved in `hw1/results/example_2_6_simulated.csv`.
- Requires scikit-learn 1.9.1 and matplotlib 3.10.8 (see `requirements.txt`).
