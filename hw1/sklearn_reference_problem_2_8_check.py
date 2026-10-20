"""Independent Problem 2.8 diagnostic; never imports the homework solver.

Run with Python containing scikit-learn. Original CSV order and percent units
are retained. Only this script's separately named diagnostic outputs are written.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np
import sklearn
from sklearn.model_selection import LeaveOneOut
from sklearn.neighbors import KNeighborsClassifier

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
PREFIX = "sklearn_reference_problem_2_8"


def load(year):
    with (ROOT / f"obesity_election_{year}.csv").open(newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 51 and len({r[3] for r in rows}) == 51
    assert sum(r[3] == "DC" for r in rows) == 1
    x = np.array([[float(r[1].rstrip("%"))] for r in rows])
    exact = [int(Decimal(r[1].rstrip("%")) * 100) for r in rows]
    y = np.array([r[2] for r in rows])
    return rows, x, exact, y


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in ROOT.rglob("*") if p.is_file()
            and not any(part in {".venv", "__pycache__", ".git"} for part in p.relative_to(ROOT).parts)
            and p.name != "sklearn_reference_problem_2_8_check.py" and not p.name.startswith(PREFIX)}


def write_csv(suffix, rows):
    path = OUT / f"{PREFIX}{suffix}.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    before = hashes()
    rows, x, exact, y = load(2000)
    test_rows, xt, _, yt = load(2004)
    baseline = OUT / f"{PREFIX}.csv"
    if baseline.exists():
        with baseline.open(newline="") as f:
            saved = {int(r["k"]): int(r["existing_custom_loocv_mistakes"]) for r in csv.DictReader(f)}
    else:
        with (OUT / "loocv_scores.csv").open(newline="") as f:
            saved = {int(r["k"]): int(r["errors"]) for r in csv.DictReader(f) if r["problem"] == "2.8"}
    folds, scores, differences, focused = [], [], [], []
    for k in range(1, 51):
        mistakes = custom_mistakes = 0
        for train, held in LeaveOneOut().split(x):
            i = int(held[0])
            assert len(train) == 50 and i not in train
            model = KNeighborsClassifier(n_neighbors=k)
            model.fit(x[train], y[train])
            pred = str(model.predict(x[held])[0])
            distances, local = model.kneighbors(x[held])
            neighbors = [int(train[j]) for j in local[0]]
            votes = Counter(str(y[j]) for j in neighbors)
            mode = max(model.classes_, key=lambda label: votes[str(label)])
            assert pred == mode, "predict/kneighbors disagree; inspect optimized prediction path"
            # Independent audit of the documented custom policy, using exact units.
            ordered = sorted((int(j) for j in train), key=lambda j: (abs(exact[j] - exact[i]), rows[j][3]))
            custom_neighbors = ordered[:k]
            custom_votes = Counter(str(y[j]) for j in custom_neighbors)
            fitting_counts = Counter(str(y[j]) for j in train)
            fallback = "R" if fitting_counts["R"] > fitting_counts["D"] else "D"
            custom_pred = fallback if custom_votes["R"] == custom_votes["D"] else max(custom_votes, key=custom_votes.get)
            # Change only the voting rule on the custom neighbor set.
            custom_neighbors_sklearn_vote = "R" if custom_votes["R"] > custom_votes["D"] else "D"
            mistakes += pred != y[i]
            custom_mistakes += custom_pred != y[i]
            fold = dict(k=k, held_out_index=i, csv_row=i + 1, state=rows[i][0], code=rows[i][3],
                        obesity_percent=float(x[i, 0]), actual=str(y[i]), sklearn_prediction=pred,
                        custom_policy_prediction=custom_pred, sklearn_mistake=int(pred != y[i]),
                        custom_mistake=int(custom_pred != y[i]), sklearn_D_votes=votes["D"],
                        sklearn_R_votes=votes["R"], custom_D_votes=custom_votes["D"],
                        custom_R_votes=custom_votes["R"], algorithm_used=model._fit_method)
            folds.append(fold)
            if k in (20, 22) and pred != custom_pred:
                focused.append(fold.copy())
            if pred != custom_pred:
                def detail(indices):
                    return [dict(index=j, state=rows[j][0], code=rows[j][3], label=str(y[j]),
                                 obesity_percent=float(x[j, 0]),
                                 exact_distance_percent=str(Decimal(abs(exact[j] - exact[i])) / 100),
                                 float_distance_percent=repr(abs(float(x[j, 0]) - float(x[i, 0]))))
                            for j in indices]
                boundary = abs(exact[ordered[k - 1]] - exact[i])
                boundary_group = [j for j in ordered if abs(exact[j] - exact[i]) == boundary]
                differences.append(dict(**fold,
                    same_neighbor_set=set(neighbors) == set(custom_neighbors),
                    custom_neighbors_with_sklearn_vote=custom_neighbors_sklearn_vote,
                    class_vote_tie=votes["D"] == votes["R"],
                    exact_boundary_tie_crosses_cutoff=(k < 50 and abs(exact[ordered[k]] - exact[i]) == boundary),
                    boundary_tied_observations=detail(boundary_group),
                    sklearn_neighbors=detail(neighbors), custom_neighbors=detail(custom_neighbors)))
        assert custom_mistakes == saved[k], (k, custom_mistakes, saved[k])
        scores.append(dict(k=k, sklearn_loocv_mistakes=int(mistakes), samples=51,
                           sklearn_loocv_error_rate=mistakes / 51,
                           existing_custom_loocv_mistakes=custom_mistakes,
                           existing_custom_loocv_error_rate=custom_mistakes / 51,
                           prediction_disagreements=sum(f["sklearn_prediction"] != f["custom_policy_prediction"] for f in folds if f["k"] == k)))
    minimum = min(s["sklearn_loocv_mistakes"] for s in scores)
    minimizers = [s["k"] for s in scores if s["sklearn_loocv_mistakes"] == minimum]
    test_scores, test_predictions = [], []
    for k in minimizers:
        model = KNeighborsClassifier(n_neighbors=k).fit(x, y)
        predictions = model.predict(xt)
        errors = int(np.count_nonzero(predictions != yt))
        test_scores.append(dict(k=k, test_mistakes=errors, samples=51, test_error_rate=errors / 51))
        for i, prediction in enumerate(predictions):
            test_predictions.append(dict(k=k, state=test_rows[i][0], code=test_rows[i][3], actual=str(yt[i]),
                                         predicted=str(prediction), mistake=int(prediction != yt[i])))
    write_csv("", scores)
    write_csv("_fold_predictions", folds)
    write_csv("_test_errors", test_scores)
    write_csv("_test_predictions", test_predictions)
    if focused:
        write_csv("_k20_k22_differences", focused)
    summary = dict(sklearn_version=sklearn.__version__, numpy_version=np.__version__,
                   class_order=KNeighborsClassifier().fit(x, y).classes_.tolist(),
                   training_samples=len(y), test_samples=len(yt), training_class_counts=dict(Counter(y)),
                   predictor="obesity percentage, float64 in percentage-point units",
                   csv_order="original supplied order; zero-based index; csv_row is one-based",
                   estimator="KNeighborsClassifier(n_neighbors=k), all other settings default",
                   minimum_loocv_mistakes=minimum, minimum_loocv_error_rate=minimum / 51,
                   all_minimizing_k=minimizers, test_errors=test_scores,
                   requested_k_scores=[s for s in scores if s["k"] in (2, 3, 5, 12, 17, 20, 22)],
                   first_prediction_disagreement=differences[0] if differences else None,
                   disagreement_count=len(differences),
                   custom_policy_audit_matches_all_50_saved_scores=True,
                   original_file_sha256=before)
    (OUT / f"{PREFIX}_differences.json").write_text(json.dumps(differences, indent=2) + "\n")
    assert hashes() == before, "An existing file changed during the diagnostic"
    summary["all_existing_files_unchanged"] = True
    (OUT / f"{PREFIX}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
