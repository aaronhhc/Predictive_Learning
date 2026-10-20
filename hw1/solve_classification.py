"""Reproduce Homework 1 Problems 2.7 and 2.8; no regression analysis."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import sklearn
from sklearn.model_selection import LeaveOneOut
from sklearn.neighbors import KNeighborsClassifier

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results"
INPUT_HASHES = {
    "Homework1.pdf": "5a9e8da0da91ef126610661b7d481d364a6d20a04e1f815194ea405ddcdd4db6",
    "obesity_election_2000.csv": "781864e47b6144ff7416594e6e5f210c2044fc8e049a7d238f7ef3dba4d08bf9",
    "obesity_election_2004.csv": "fcbb3ce3d0c3a0765326848b79e39ac5f414d0b8a2c9a2478a7f861f7ce1067d",
}


@dataclass(frozen=True)
class Observation:
    name: str
    x: int  # Hundredths of a percentage point, for exact distance comparisons.
    label: str
    code: str


def check_originals() -> None:
    for name, expected in INPUT_HASHES.items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Original input changed: {name}")


def load(year: int) -> list[Observation]:
    observations = []
    with (ROOT / f"obesity_election_{year}.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.reader(source):
            if len(row) != 4 or any(not field.strip() for field in row):
                raise ValueError(f"Malformed row: {row}")
            name, percent, label, code = row
            if not percent.endswith("%") or label not in {"R", "D"}:
                raise ValueError(f"Invalid percentage or label: {row}")
            scaled = Decimal(percent[:-1]) * 100
            if not scaled.is_finite() or scaled != scaled.to_integral_value() or not 0 <= scaled <= 10000:
                raise ValueError(f"Invalid percentage precision/range: {percent}")
            observations.append(Observation(name, int(scaled), label, code))
    if len(observations) != 51 or len({r.code for r in observations}) != 51:
        raise ValueError("Expected 51 unique jurisdictions")
    if len({r.name for r in observations}) != 51 or sum(r.code == "DC" for r in observations) != 1:
        raise ValueError("Expected 50 states plus DC")
    return observations


def features(observations: list[Observation]) -> np.ndarray:
    return np.array([[row.x / 100] for row in observations], dtype=np.float64)


def select_k(training: list[Observation]) -> tuple[int, list[int], list[int]]:
    """True LOOCV using sklearn defaults and training data only."""
    x = features(training)
    labels = np.array([row.label for row in training])
    errors = []
    for k in range(1, len(training)):
        mistakes = 0
        for fitting, held_out in LeaveOneOut().split(x):
            assert len(fitting) == 50 and len(held_out) == 1
            model = KNeighborsClassifier(n_neighbors=k)
            model.fit(x[fitting], labels[fitting])
            mistakes += int(model.predict(x[held_out])[0] != labels[held_out][0])
        errors.append(mistakes)
    minimizers = [k for k, error in enumerate(errors, start=1) if error == min(errors)]
    return min(minimizers), minimizers, errors


def analyze(problem: str, training: list[Observation], test: list[Observation], train_year: int, test_year: int) -> dict:
    k, minimizers, loo_errors = select_k(training)
    model = KNeighborsClassifier(n_neighbors=k)
    model.fit(features(training), [row.label for row in training])
    predictions = model.predict(features(test)).tolist()
    test_errors = sum(prediction != row.label for prediction, row in zip(predictions, test))
    return {
        "problem": problem, "training_year": train_year, "test_year": test_year,
        "training_samples": len(training), "test_samples": len(test),
        "selected_k": k, "all_minimizing_k": minimizers,
        "loocv_errors": min(loo_errors), "loocv_error": min(loo_errors) / len(training),
        "test_errors": test_errors, "test_error": test_errors / len(test),
        "loocv_errors_by_k": loo_errors, "test_predictions": predictions,
    }


def write_csv(path: Path, header: list[str], rows: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(header)
        writer.writerows(rows)


def plot(results: list[dict]) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for axis, result in zip(axes, results):
        axis.plot(range(1, 51), [100 * e / 51 for e in result["loocv_errors_by_k"]], color="#245a81", linewidth=1.5)
        axis.scatter(result["selected_k"], 100 * result["loocv_error"], color="#b54b23", zorder=3,
                     label=f'Selected k = {result["selected_k"]}')
        axis.set_title(f'Problem {result["problem"]}: train {result["training_year"]}')
        axis.set_xlabel("Number of neighbors k")
        axis.set_xlim(1, 50)
        axis.grid(alpha=0.25)
        axis.legend(frameon=False)
    axes[0].set_ylabel("Leave-one-out classification error (%)")
    fig.tight_layout()
    for extension in ("png", "svg", "pdf"):
        fig.savefig(OUTPUT / f"loocv_errors.{extension}", dpi=180)
    plt.close(fig)
    return matplotlib.__version__


def report(results: list[dict]) -> str:
    lines = ["# Homework 1 — Problems 2.7 and 2.8", "",
        "Both original datasets contain 50 states plus DC (51 observations). Obesity percentage is the sole predictor; supplied R/D labels and original row order are retained.", "",
        "## Method", "",
        "The classifier is scikit-learn's standard KNeighborsClassifier with default uniform weights and all other estimator settings at their defaults. LeaveOneOut evaluates k = 1,…,50 using the training year only: each fit uses exactly 50 observations and predicts the held-out observation. Among tied minimum LOOCV errors, the smallest k is selected as an implementation convention. The selected classifier is fitted on all 51 training observations; test labels are used only for scoring.", "",
        "## Results", "",
        "| Problem | Training → test | Selected k | LOOCV error | Test error |",
        "|---|---|---:|---:|---:|"]
    for r in results:
        lines.append(f'| {r["problem"]} | {r["training_year"]} → {r["test_year"]} | {r["selected_k"]} | {r["loocv_errors"]}/51 ({100*r["loocv_error"]:.2f}%) | {r["test_errors"]}/51 ({100*r["test_error"]:.2f}%) |')
    for r in results:
        lines += ["", f'Problem {r["problem"]}: all minimizing k values are ' + ", ".join(map(str, r["all_minimizing_k"])) + "."]
    lines += ["", "![LOOCV errors](results/loocv_errors.png)", "",
        "## Discussion", "",
        "Within-year LOOCV error is lower than cross-year test error in Problem 2.7. Problem 2.8 has equal LOOCV and test error. Always predicting the training majority class (R) gives test errors of 21/51 (41.18%) and 19/51 (37.25%), respectively: the selected model is worse than this baseline in Problem 2.7 and matches it in Problem 2.8. Identical obesity values can have opposite labels, and changes across years limit prediction from this sole predictor. These tests evaluate transfer across years for the same jurisdictions. Minimum LOOCV error is used for selection and is not an independent post-selection estimate.", "",
        "## Reproduction", "", f"Checked with Python {platform.python_version()} and scikit-learn {sklearn.__version__}.", "",
        "```sh", "python3 -m venv .venv", ".venv/bin/python -m pip install -r requirements-lock.txt",
        ".venv/bin/python solve_classification.py", ".venv/bin/python -m unittest -v test_classification.py", "```", "",
        "All 100 LOOCV counts and all 102 selected-model test predictions are checked against separately computed sklearn reference outputs. Checks also confirm that changing test labels cannot change model selection or predictions. Original input hashes are checked before and after the run.", ""]
    return "\n".join(lines)


def main() -> None:
    check_originals()
    data = {year: load(year) for year in (2000, 2004)}
    if {r.code for r in data[2000]} != {r.code for r in data[2004]}:
        raise ValueError("Jurisdiction sets differ")
    results = [analyze("2.7", data[2004], data[2000], 2004, 2000),
               analyze("2.8", data[2000], data[2004], 2000, 2004)]
    OUTPUT.mkdir(exist_ok=True)
    write_csv(OUTPUT / "summary.csv", ["problem", "training_year", "test_year", "selected_k", "loocv_errors", "loocv_error", "test_errors", "test_error"],
              [[r[key] for key in ("problem", "training_year", "test_year", "selected_k", "loocv_errors", "loocv_error", "test_errors", "test_error")] for r in results])
    write_csv(OUTPUT / "loocv_scores.csv", ["problem", "training_year", "k", "errors", "samples", "error_rate"],
              [[r["problem"], r["training_year"], k, error, 51, error / 51] for r in results for k, error in enumerate(r["loocv_errors_by_k"], start=1)])
    write_csv(OUTPUT / "test_predictions.csv", ["problem", "test_year", "jurisdiction", "code", "obesity_percent", "actual", "predicted", "correct"],
              [[r["problem"], r["test_year"], observation.name, observation.code, f"{observation.x / 100:.2f}", observation.label, prediction, prediction == observation.label]
               for r in results for observation, prediction in zip(data[r["test_year"]], r["test_predictions"])])
    matplotlib_version = plot(results)
    (OUTPUT / "results.json").write_text(json.dumps({"python": platform.python_version(), "matplotlib": matplotlib_version, "sklearn": sklearn.__version__,
        "input_sha256": INPUT_HASHES, "choices": {"k_range": [1, 50], "estimator": "sklearn.neighbors.KNeighborsClassifier",
        "weights": "uniform", "other_estimator_settings": "sklearn defaults", "cv": "sklearn.model_selection.LeaveOneOut",
        "predictor": "obesity percentage as float64 percentage points", "row_order": "original CSV order",
        "class_order": ["D", "R"], "selection_tie": "smallest k"},
        "results": results}, indent=2) + "\n")
    (ROOT / "classification_report.md").write_text(report(results))
    check_originals()
    for r in results:
        print(f'Problem {r["problem"]}: k={r["selected_k"]}; tied minima={r["all_minimizing_k"]}; '
              f'LOOCV={r["loocv_errors"]}/51; test={r["test_errors"]}/51')


if __name__ == "__main__":
    main()
