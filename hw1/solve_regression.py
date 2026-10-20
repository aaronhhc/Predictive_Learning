"""Homework 1 Problems 2.11/2.12, using the user-supplied course criterion."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
from numpy.polynomial import Legendre, Polynomial

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results"
DATA = OUTPUT / "example_2_6_simulated.csv"
DATA_SEED = 20261006
FOLD_SEED = 212
FAMILIES = ("trigonometric", "algebraic")


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(columns)
        writer.writerows(rows)


def dataset():
    """Save one realization once; subsequent runs reuse the saved observations."""
    if not DATA.exists():
        rng = np.random.Generator(np.random.PCG64(DATA_SEED))
        x = rng.uniform(0.0, 1.0, size=10)
        noise = rng.normal(loc=0.0, scale=0.5, size=10)
        truth = x**2 + 0.1 * x
        y = truth + noise
        write_csv(DATA, ["sample_id", "x", "y", "noise", "noiseless_mean"],
                  [[i, float(x[i]), float(y[i]), float(noise[i]), float(truth[i])] for i in range(10)])
    with DATA.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 10 or [int(r["sample_id"]) for r in rows] != list(range(10)):
        raise ValueError("Expected exactly ten ordered samples")
    x = np.array([float(r["x"]) for r in rows])
    y = np.array([float(r["y"]) for r in rows])
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or not np.all((0 <= x) & (x <= 1)):
        raise ValueError("Invalid simulated observations")
    return x, y


def design(x, m, family):
    x = np.asarray(x, dtype=float)
    if family == "trigonometric":
        return np.column_stack([np.ones(len(x))] + [np.cos(2 * np.pi * i * x) for i in range(1, m + 1)])
    if family == "algebraic":
        # An equivalent polynomial basis improves conditioning without changing DoF.
        return np.polynomial.legendre.legvander(2 * x - 1, m)
    raise ValueError(f"Unknown family: {family}")


def schwarz_multiplier(dof, n):
    if not 0 < dof < n:
        raise ValueError("Course criterion requires 0 < DoF < n")
    p = dof / n
    return 1 + (p / (1 - p)) * math.log(n)


def fit(x, y, m, family):
    if m < 0 or m + 1 >= len(x):
        raise ValueError("Require nonnegative m and DoF=m+1<n")
    matrix = design(x, m, family)
    coef, _, rank, singular = np.linalg.lstsq(matrix, y, rcond=None)
    if rank != m + 1:
        raise ValueError(f"Rank-deficient {family} model at m={m}")
    residual = np.asarray(y) - matrix @ coef
    empirical = float(np.mean(residual**2))
    multiplier = schwarz_multiplier(m + 1, len(x))
    if family == "algebraic":
        # Convert coefficients to the assignment's powers of x for reporting only.
        power_z = Legendre(coef).convert(kind=Polynomial)
        power_x = power_z(Polynomial([-1.0, 2.0]))
        weights = power_x.coef.tolist()
    else:
        weights = coef.tolist()
    return {"family": family, "m": m, "dof": m + 1, "n": len(x), "p": (m + 1) / len(x),
            "training_mse": empirical, "schwarz_multiplier": multiplier,
            "estimated_risk": multiplier * empirical,
            "rank": int(rank), "condition_number": float(singular[0] / singular[-1]),
            "fit_basis_coefficients": coef.tolist(), "assignment_basis_weights": weights}


def predict(model, x):
    return design(x, model["m"], model["family"]) @ np.array(model["fit_basis_coefficients"])


def select(x, y, family):
    candidates = [fit(x, y, m, family) for m in range(len(x) - 1)]
    # Candidates are ordered; an exactly tied risk selects the smallest m.
    selected = min(candidates, key=lambda row: (row["estimated_risk"], row["m"]))
    return selected, candidates


def make_folds():
    rng = np.random.Generator(np.random.PCG64(FOLD_SEED))
    return [group.tolist() for group in np.split(rng.permutation(10), 5)]


def cross_validate(x, y, folds):
    if len(folds) != 5 or any(len(fold) != 2 for fold in folds) or sorted(sum(folds, [])) != list(range(10)):
        raise ValueError("Require five disjoint two-observation folds covering all ten observations")
    fold_rows, prediction_rows, candidate_rows, models = [], [], [], []
    for fold_id, held in enumerate(folds, start=1):
        training = [i for i in range(10) if i not in held]
        for family in FAMILIES:
            selected, candidates = select(x[training], y[training], family)
            predictions = predict(selected, x[held])
            errors = (y[held] - predictions)**2
            fold_rows.append({"family": family, "fold": fold_id, "training_sample_ids": training,
                              "held_out_sample_ids": held, "selected_m": selected["m"],
                              "dof": selected["dof"], "n": selected["n"],
                              "selected_training_mse": selected["training_mse"],
                              "selected_estimated_risk": selected["estimated_risk"],
                              "fold_sse": float(errors.sum()), "fold_mse": float(errors.mean())})
            for i, prediction, error in zip(held, predictions, errors):
                prediction_rows.append({"family": family, "fold": fold_id, "sample_id": i,
                                        "x": float(x[i]), "actual_y": float(y[i]),
                                        "predicted_y": float(prediction), "squared_error": float(error)})
            candidate_rows.extend([dict(row, fold=fold_id) for row in candidates])
            models.append(dict(selected, fold=fold_id, training_sample_ids=training, held_out_sample_ids=held))
    cv_mse = {family: float(np.mean([row["squared_error"] for row in prediction_rows if row["family"] == family]))
              for family in FAMILIES}
    return {"fold_results": fold_rows, "predictions": prediction_rows, "candidates": candidate_rows,
            "selected_models": models, "cv_mse": cv_mse}


def table_row(model):
    return [model[k] for k in ["m", "dof", "n", "p", "training_mse", "schwarz_multiplier", "estimated_risk", "rank", "condition_number"]]


def figures(x, y, full, cv):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    grid = np.linspace(0, 1, 501)
    for family in FAMILIES:
        selected = full[family]["selected"]
        candidates = full[family]["candidates"]
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.7))
        axes[0].plot([r["m"] for r in candidates], [r["training_mse"] for r in candidates], "o-", label="Training MSE")
        axes[0].plot([r["m"] for r in candidates], [r["estimated_risk"] for r in candidates], "s-", label="Schwartz estimated risk")
        axes[0].axvline(selected["m"], color="#777777", linestyle="--", label=f'Selected m={selected["m"]}')
        axes[0].set(xlabel="Order / degree m", ylabel="Mean squared error / estimated risk", xticks=range(9))
        axes[0].legend(frameon=False, fontsize=8)
        axes[1].scatter(x, y, color="#333333", label="Simulated observations", zorder=3)
        axes[1].plot(grid, grid**2 + 0.1 * grid, "--", color="#777777", label="Generating mean")
        axes[1].plot(grid, predict(selected, grid), color="#245a81", label=f'Selected fit (m={selected["m"]})')
        axes[1].set(xlabel="x", ylabel="y", xlim=(0, 1))
        axes[1].set_title("Full input domain", fontsize=10)
        axes[1].legend(frameon=False, fontsize=8)
        observed_grid = np.linspace(x.min(), x.max(), 501)
        axes[2].scatter(x, y, color="#333333", label="Simulated observations", zorder=3)
        axes[2].plot(observed_grid, observed_grid**2 + 0.1 * observed_grid, "--", color="#777777", label="Generating mean")
        axes[2].plot(observed_grid, predict(selected, observed_grid), color="#245a81", label="Selected fit")
        axes[2].set(xlabel="x", ylabel="y", xlim=(x.min(), x.max()))
        axes[2].set_title("Observed input range", fontsize=10)
        for axis in axes:
            axis.grid(alpha=0.2)
        fig.suptitle(f"Problem 2.11: {family} models (simulated realization)")
        fig.tight_layout()
        for extension in ("png", "svg", "pdf"):
            fig.savefig(OUTPUT / f"problem_2_11_{family}.{extension}", dpi=180)
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    positions = np.arange(1, 6)
    for offset, family in [(-0.18, "trigonometric"), (0.18, "algebraic")]:
        rows = [r for r in cv["fold_results"] if r["family"] == family]
        axes[0].bar(positions + offset, [r["fold_mse"] for r in rows], width=0.36, label=family.capitalize())
        values = sorted([r for r in cv["predictions"] if r["family"] == family], key=lambda row: row["sample_id"])
        axes[1].scatter([r["x"] for r in values], [r["predicted_y"] for r in values], label=family.capitalize())
    axes[0].set(xlabel="Outer fold", ylabel="Held-out MSE (log scale)", xticks=positions, yscale="log")
    axes[1].scatter(x, y, marker="x", color="black", label="Observed y")
    axes[1].set(xlabel="x", ylabel="Held-out prediction / observed y")
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=8)
    fig.suptitle("Problem 2.12: five-fold predictions (same simulated observations)")
    fig.tight_layout()
    for extension in ("png", "svg", "pdf"):
        fig.savefig(OUTPUT / f"problem_2_12_cv.{extension}", dpi=180)
    plt.close(fig)
    return matplotlib.__version__


def report(full, cv, folds):
    lines = ["# Homework 1 — Problems 2.11 and 2.12", "",
        "Since the homework specifies the data-generating process but does not provide the numerical realization, "
        "a reproducible n = 10 realization was generated with random seed 20261006 and reused in Problems 2.11 and 2.12.", "",
        f"Dataset: n = 10, x ~ Uniform[0,1], y = x² + 0.1x + ε, ε ~ N(0,0.25). "
        f"Noise standard deviation is 0.5. NumPy Generator(PCG64), seed {DATA_SEED}, draws all ten x values "
        "first and then ten independent noise values. The saved `results/example_2_6_simulated.csv` "
        "is reused unchanged for both problems and on subsequent runs.", "",
        "## Course criterion and fitting", "",
        "The supplied course-specific equation is used directly:", "",
        "$$p=\\frac{\\mathrm{DoF}}{n},\\qquad r(p,n)=1+\\frac{p}{1-p}\\ln n,\\qquad "
        "\\widehat R=r(p,n)R_{\\mathrm{emp}},\\qquad "
        "R_{\\mathrm{emp}}=\\frac1n\\sum_{j=1}^n(y_j-\\widehat f(x_j))^2.$$", "",
        "Both families have DoF = m + 1. The trigonometric model contains only an intercept and "
        "cos(2πix), i = 1,…,m; no sine terms are added. Algebraic models span 1,x,…,x^m. "
        "Fits use SVD-based NumPy least squares. Algebraic fitting uses Legendre polynomials of 2x−1, "
        "an equivalent basis of the same degree-m polynomial space, to improve conditioning. "
        "Reported assignment-basis coefficients are converted back to powers of x; predictions use the stable fitting basis. "
        "No regularization or generic BIC is used. An exactly tied estimated risk is resolved by choosing the smallest m.", "",
        "## Problem 2.11", "",
        "With n = 10, admissible models have m = 0,…,8 and DoF < 10. The following tables report every candidate.", ""]
    for family in FAMILIES:
        chosen = full[family]["selected"]
        lines += [f"### {family.capitalize()}", "",
                  "| m | DoF | Training MSE R_emp | Multiplier r(p,10) | Estimated risk R_hat |",
                  "|---:|---:|---:|---:|---:|"]
        for row in full[family]["candidates"]:
            lines.append(f'| {row["m"]} | {row["dof"]} | {row["training_mse"]:.9g} | {row["schwarz_multiplier"]:.9g} | {row["estimated_risk"]:.9g} |')
        lines += ["", f'Selected m = **{chosen["m"]}**, DoF = {chosen["dof"]}, '
                  f'estimated risk = {chosen["estimated_risk"]:.9g}.', "",
                  f"![{family.capitalize()} model selection and selected fit](results/problem_2_11_{family}.png)", ""]
    lines += ["The minimum Schwartz values can be compared as estimates under the supplied criterion, "
        "but two within-family selections alone do not establish which family has the lowest true predictive risk. "
        "Selection uses the same small training dataset, and the risk estimates depend on the criterion's assumptions. "
        "Independent predictive evaluation is needed to support a family comparison; Problem 2.12 supplies held-out predictions.", "",
        "## Problem 2.12", "",
        f"A separate PCG64 generator with seed {FOLD_SEED} permutes sample IDs 0,…,9 and groups consecutive "
        "pairs into five outer folds. Both families use exactly the same folds. For every fold, only the eight "
        "training observations are used to select m = 0,…,6, using n = 8 and DoF = m + 1 < 8. "
        "The selected fit predicts the two held-out observations. All ten squared prediction errors are pooled "
        "to obtain CV MSE; since fold sizes are equal, this also equals the mean of the five fold MSEs.", "",
        "| Fold | Held-out IDs | Trig. selected m | Trig. fold MSE | Alg. selected m | Alg. fold MSE |",
        "|---:|---|---:|---:|---:|---:|"]
    for fold_id, held in enumerate(folds, start=1):
        rows = {r["family"]: r for r in cv["fold_results"] if r["fold"] == fold_id}
        t, a = rows["trigonometric"], rows["algebraic"]
        lines.append(f'| {fold_id} | {", ".join(map(str, held))} | {t["selected_m"]} | {t["fold_mse"]:.9g} | {a["selected_m"]} | {a["fold_mse"]:.9g} |')
    lines += ["", "| Family | Five-fold CV MSE |", "|---|---:|"]
    for family in FAMILIES:
        lines.append(f'| {family.capitalize()} | {cv["cv_mse"][family]:.9g} |')
    better = min(FAMILIES, key=lambda family: cv["cv_mse"][family])
    difference = abs(cv["cv_mse"]["trigonometric"] - cv["cv_mse"]["algebraic"])
    lines += ["", f"**{better.capitalize()} models perform better on this realization and fold partition**, "
        f"with CV MSE lower by {difference:.9g}. This evaluates each family's complete Schwartz-selection "
        "procedure rather than a degree chosen using all ten observations. The folds were fixed before "
        "looking at predictive errors. No outer held-out observation was used to fit or select a model "
        "within its fold; the pooled held-out errors are used to compare the families.", "",
        "![Five-fold results](results/problem_2_12_cv.png)", "",
        "## Validation and limitations", "",
        "Independent checks compare the multiplier to 1 + DoF·ln(n)/(n−DoF), recompute all candidate "
        "fits by QR in a separate polynomial basis, verify held-out predictions and pooled errors, check "
        "DoF and rank, and change held-out labels to confirm the corresponding fold's selection cannot change. "
        "Every sample is held out once per family and both families use identical training/test fold IDs.", "",
        "This comparison is based on one simulated dataset of ten observations and one five-fold partition. "
        "Fold errors and selected orders can vary with the realization or partition; this result does not "
        "establish universal superiority or statistical significance. High-order fits may be numerically sensitive "
        "and unstable between samples; saved candidate tables include matrix rank and condition number. "
        "The course multiplier is undefined at DoF = n, so those models are excluded rather than evaluated.", "",
        "The large trigonometric CV error is dominated by fold 2 (fold MSE 111.460273): the prediction "
        "for sample 6 is approximately 14.8994, compared with observed y = 0.520865. Independent QR "
        "checks reproduce this result. The algebraic full-data m = 7 fit also exhibits a large boundary "
        "excursion near x = 0, outside the observed input range (approximately 0.211–0.994). The figures "
        "show both the full domain and a separate view of the observed range. CV here assesses held-out "
        "observations at their sampled locations and does not establish reliable behavior everywhere on [0,1]. "
        "Furthermore, every specified cosine-only model satisfies f(x) = f(1−x), whereas the generating "
        "mean x² + 0.1x does not; the two families therefore have different approximation limitations.", "",
        "## Reproduction and saved results", "",
        "Use the existing environment and dependency lockfile:", "", "```sh",
        ".venv/bin/python solve_regression.py", ".venv/bin/python -m unittest -v test_regression.py", "```", "",
        "CSV tables contain full-precision values; report tables are rounded for display. JSON includes "
        "seeds, versions, dataset hash, all candidate fits, stable-basis and assignment-basis coefficients, "
        "selected models, folds, and held-out predictions. PNG/SVG/PDF figures accompany the tables. "
        "Original PDF/CSV files and all classification results are preserved.", "",
        "Created files:", "",
        "- `solve_regression.py`, `test_regression.py`, `regression_report.md`",
        "- `results/example_2_6_simulated.csv`",
        "- `results/problem_2_11_trigonometric.csv`, `results/problem_2_11_algebraic.csv`",
        "- `results/problem_2_12_candidates.csv`, `results/problem_2_12_folds.csv`, `results/problem_2_12_predictions.csv`",
        "- `results/regression_summary.csv`, `results/regression_results.json`, `results/regression_validation.txt`",
        "- `results/problem_2_11_trigonometric.png`, `.svg`, `.pdf`",
        "- `results/problem_2_11_algebraic.png`, `.svg`, `.pdf`",
        "- `results/problem_2_12_cv.png`, `.svg`, `.pdf`", ""]
    return "\n".join(lines)


def main():
    OUTPUT.mkdir(exist_ok=True)
    x, y = dataset()
    full = {}
    for family in FAMILIES:
        chosen, candidates = select(x, y, family)
        full[family] = {"selected": chosen, "candidates": candidates}
        write_csv(OUTPUT / f"problem_2_11_{family}.csv",
                  ["m", "dof", "n", "p", "training_mse", "schwarz_multiplier", "estimated_risk", "rank", "condition_number"],
                  [table_row(row) for row in candidates])
    folds = make_folds()
    cv = cross_validate(x, y, folds)
    fold_columns = ["family", "fold", "training_sample_ids", "held_out_sample_ids", "selected_m", "dof", "n",
                    "selected_training_mse", "selected_estimated_risk", "fold_sse", "fold_mse"]
    write_csv(OUTPUT / "problem_2_12_folds.csv", fold_columns,
              [[json.dumps(row[key]) if isinstance(row[key], list) else row[key] for key in fold_columns] for row in cv["fold_results"]])
    prediction_columns = ["family", "fold", "sample_id", "x", "actual_y", "predicted_y", "squared_error"]
    write_csv(OUTPUT / "problem_2_12_predictions.csv", prediction_columns,
              [[row[key] for key in prediction_columns] for row in cv["predictions"]])
    write_csv(OUTPUT / "problem_2_12_candidates.csv",
              ["family", "fold", "m", "dof", "n", "p", "training_mse", "schwarz_multiplier", "estimated_risk", "rank", "condition_number"],
              [[row["family"], row["fold"], *table_row(row)] for row in cv["candidates"]])
    write_csv(OUTPUT / "regression_summary.csv", ["family", "problem_2_11_selected_m", "problem_2_11_estimated_risk", "problem_2_12_cv_mse"],
              [[family, full[family]["selected"]["m"], full[family]["selected"]["estimated_risk"], cv["cv_mse"][family]] for family in FAMILIES])
    mpl_version = figures(x, y, full, cv)
    result = {"data_provenance": "Simulated homework distribution; not original Example 2.6 observations",
              "data_seed": DATA_SEED, "fold_seed": FOLD_SEED, "rng": "NumPy Generator(PCG64)",
              "draw_order": "10 Uniform(0,1) draws, then 10 Normal(0,0.5 standard deviation) draws",
              "data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
              "versions": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": mpl_version},
              "criterion": "R_hat = (1 + (p/(1-p))*ln(n))*R_emp; p=(m+1)/n", "selection_tie": "smallest m",
              "folds": folds, "problem_2_11": full, "problem_2_12": cv}
    (OUTPUT / "regression_results.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "regression_report.md").write_text(report(full, cv, folds))
    for family in FAMILIES:
        print(f'{family}: Problem 2.11 m={full[family]["selected"]["m"]}; '
              f'Problem 2.12 CV MSE={cv["cv_mse"][family]:.12g}; '
              f'fold m={[r["selected_m"] for r in cv["fold_results"] if r["family"] == family]}')


if __name__ == "__main__":
    main()
