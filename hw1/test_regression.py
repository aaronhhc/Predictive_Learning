"""Independent numerical and isolation checks of saved regression results."""

import csv
import hashlib
import json
import math
import unittest

import numpy as np

import solve_classification
import solve_regression as solution


def reference_design(x, m, family):
    # Explicit shifted monomials differ from the Legendre fitting basis.
    if family == "algebraic":
        return np.array([[(2 * value - 1)**i for i in range(m + 1)] for value in x])
    return np.array([[1.0] + [math.cos(2 * math.pi * i * value) for i in range(1, m + 1)] for value in x])


def reference_fit(x, y, m, family):
    matrix = reference_design(x, m, family)
    q, r = np.linalg.qr(matrix, mode="reduced")
    coef = np.linalg.solve(r, q.T @ y)
    mse = float(sum((y - matrix @ coef)**2) / len(y))
    dof, n = m + 1, len(x)
    multiplier = 1 + dof * math.log(n) / (n - dof)
    return {"m": m, "coef": coef, "mse": mse, "multiplier": multiplier, "risk": mse * multiplier}


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads((solution.OUTPUT / "regression_results.json").read_text())
        cls.x, cls.y = solution.dataset()

    def test_data_provenance_exact_reproduction_and_reuse(self):
        rng = np.random.Generator(np.random.PCG64(20261006))
        expected_x = rng.uniform(0, 1, 10)
        noise = rng.normal(0, 0.5, 10)
        expected_y = expected_x**2 + 0.1 * expected_x + noise
        np.testing.assert_array_equal(self.x, expected_x)
        np.testing.assert_array_equal(self.y, expected_y)
        before = solution.DATA.read_bytes()
        solution.dataset()
        self.assertEqual(before, solution.DATA.read_bytes())
        self.assertEqual(hashlib.sha256(before).hexdigest(), self.saved["data_sha256"])
        self.assertIn("not original", self.saved["data_provenance"])
        with solution.DATA.open(newline="") as source:
            rows = list(csv.DictReader(source))
        np.testing.assert_array_equal([float(r["noise"]) for r in rows], noise)

    def test_course_equation_and_domain(self):
        for n in (8, 10):
            for dof in range(1, n):
                expected = 1 + dof * math.log(n) / (n - dof)
                self.assertAlmostEqual(solution.schwarz_multiplier(dof, n), expected, places=12)
        self.assertEqual(solution.schwarz_multiplier(5, 10), 1 + math.log(10))
        for dof in (0, 10, 11):
            with self.assertRaises(ValueError):
                solution.schwarz_multiplier(dof, 10)

    def verify_candidates(self, rows, x, y, family):
        self.assertEqual([row["m"] for row in rows], list(range(len(x) - 1)))
        references = []
        for row in rows:
            m = row["m"]
            self.assertEqual(row["dof"], m + 1)
            self.assertEqual(row["rank"], m + 1)
            self.assertEqual(row["n"], len(x))
            self.assertLess(row["dof"], row["n"])
            self.assertEqual(row["p"], (m + 1) / len(x))
            ref = reference_fit(x, y, m, family)
            references.append(ref)
            np.testing.assert_allclose([row["training_mse"], row["schwarz_multiplier"], row["estimated_risk"]],
                                       [ref["mse"], ref["multiplier"], ref["risk"]], rtol=1e-8, atol=1e-10)
            np.testing.assert_allclose(solution.predict(row, x), reference_design(x, m, family) @ ref["coef"],
                                       rtol=1e-8, atol=1e-9)
        return min(references, key=lambda row: (row["risk"], row["m"]))

    def test_problem_2_11_all_candidates_and_selected_models(self):
        for family in solution.FAMILIES:
            rows = self.saved["problem_2_11"][family]
            best = self.verify_candidates(rows["candidates"], self.x, self.y, family)
            self.assertEqual(best["m"], rows["selected"]["m"])
            selected = rows["selected"]
            if family == "algebraic":
                np.testing.assert_allclose(np.polynomial.polynomial.polyval(self.x, selected["assignment_basis_weights"]),
                                           solution.predict(selected, self.x), rtol=1e-7, atol=1e-8)

    def test_problem_2_12_folds_candidates_predictions_and_aggregation(self):
        cv = self.saved["problem_2_12"]
        folds = self.saved["folds"]
        permutation = np.random.Generator(np.random.PCG64(212)).permutation(10).tolist()
        self.assertEqual(folds, [permutation[i:i + 2] for i in range(0, 10, 2)])
        self.assertEqual(sorted(sum(folds, [])), list(range(10)))
        for family in solution.FAMILIES:
            squared_errors = []
            for fold_id, held in enumerate(folds, start=1):
                training = [i for i in range(10) if i not in held]
                rows = [row for row in cv["candidates"] if row["family"] == family and row["fold"] == fold_id]
                best = self.verify_candidates(rows, self.x[training], self.y[training], family)
                recorded = next(row for row in cv["fold_results"] if row["family"] == family and row["fold"] == fold_id)
                self.assertEqual(recorded["selected_m"], best["m"])
                self.assertEqual(recorded["training_sample_ids"], training)
                self.assertEqual(recorded["held_out_sample_ids"], held)
                self.assertEqual(recorded["n"], 8)
                predictions = reference_design(self.x[held], best["m"], family) @ best["coef"]
                errors = (self.y[held] - predictions)**2
                squared_errors.extend(errors)
                stored = [row for row in cv["predictions"] if row["family"] == family and row["fold"] == fold_id]
                self.assertEqual([row["sample_id"] for row in stored], held)
                np.testing.assert_allclose([row["predicted_y"] for row in stored], predictions, rtol=1e-8, atol=1e-9)
                np.testing.assert_allclose([row["squared_error"] for row in stored], errors, rtol=1e-8, atol=1e-9)
                np.testing.assert_allclose([recorded["fold_sse"], recorded["fold_mse"]], [sum(errors), np.mean(errors)], rtol=1e-8)
            np.testing.assert_allclose(cv["cv_mse"][family], np.mean(squared_errors), rtol=1e-8)
            self.assertEqual(sorted(row["sample_id"] for row in cv["predictions"] if row["family"] == family), list(range(10)))

    def test_held_out_inputs_and_labels_cannot_influence_fold_selection(self):
        folds = self.saved["folds"]
        original = solution.cross_validate(self.x, self.y, folds)
        for fold_id, held in enumerate(folds, start=1):
            changed_x, changed_y = self.x.copy(), self.y.copy()
            changed_x[held] += 0.0001
            changed_y[held] += 1000
            altered = solution.cross_validate(changed_x, changed_y, folds)
            for family in solution.FAMILIES:
                before = next(row for row in original["selected_models"] if row["family"] == family and row["fold"] == fold_id)
                after = next(row for row in altered["selected_models"] if row["family"] == family and row["fold"] == fold_id)
                self.assertEqual(before, after)
                for row in before["held_out_sample_ids"]:
                    self.assertNotIn(row, before["training_sample_ids"])

    def test_saved_csv_tables_match_full_precision_json(self):
        cv = self.saved["problem_2_12"]
        for family in solution.FAMILIES:
            with (solution.OUTPUT / f"problem_2_11_{family}.csv").open(newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 9)
            for row, model in zip(rows, self.saved["problem_2_11"][family]["candidates"]):
                for field in row:
                    self.assertEqual(float(row[field]), model[field])
        for filename, key, numeric in [
            ("problem_2_12_candidates.csv", "candidates", ["m", "dof", "n", "training_mse", "schwarz_multiplier", "estimated_risk"]),
            ("problem_2_12_predictions.csv", "predictions", ["sample_id", "x", "actual_y", "predicted_y", "squared_error"]),
            ("problem_2_12_folds.csv", "fold_results", ["selected_m", "dof", "n", "fold_mse", "fold_sse"]),
        ]:
            with (solution.OUTPUT / filename).open(newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), len(cv[key]))
            for row, model in zip(rows, cv[key]):
                self.assertEqual(row["family"], model["family"])
                self.assertEqual(int(row["fold"]), model["fold"])
                for field in numeric:
                    self.assertEqual(float(row[field]), model[field])

    def test_original_inputs_unchanged(self):
        solve_classification.check_originals()


if __name__ == "__main__":
    unittest.main()
