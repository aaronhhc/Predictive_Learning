"""Validate final sklearn results against separately computed reference files."""
import csv
import unittest
from collections import Counter
from dataclasses import replace
from unittest.mock import patch

import solve_classification as solution


class ClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {}
        for problem, train_year, test_year in [("2.7", 2004, 2000), ("2.8", 2000, 2004)]:
            cls.results[problem] = solution.analyze(
                problem, solution.load(train_year), solution.load(test_year), train_year, test_year)

    def test_original_data_integrity_and_counts(self):
        solution.check_originals()
        for year, counts in [(2000, {"R": 30, "D": 21}), (2004, {"R": 32, "D": 19})]:
            rows = solution.load(year)
            self.assertEqual(len(rows), 51)
            self.assertEqual(Counter(row.label for row in rows), counts)

    def test_all_scores_and_predictions_against_independent_references(self):
        for problem, result in self.results.items():
            prefix = "sklearn_reference_problem_" + problem.replace(".", "_")
            with (solution.OUTPUT / f"{prefix}.csv").open(newline="") as source:
                scores = list(csv.DictReader(source))
            self.assertEqual(result["loocv_errors_by_k"], [int(r["sklearn_loocv_mistakes"]) for r in scores])
            with (solution.OUTPUT / f"{prefix}_test_predictions.csv").open(newline="") as source:
                predictions = [r["predicted"] for r in csv.DictReader(source) if int(r["k"]) == result["selected_k"]]
            self.assertEqual(result["test_predictions"], predictions)

    def test_verified_minima_and_smallest_k_convention(self):
        for problem, minima, cv_errors, test_errors in [
            ("2.7", [7, 9, 20, 22], 14, 27),
            ("2.8", [16, 24, 25, 26, 27, 28], 19, 19),
        ]:
            result = self.results[problem]
            self.assertEqual(result["all_minimizing_k"], minima)
            self.assertEqual(result["selected_k"], min(minima))
            self.assertEqual(result["loocv_errors"], cv_errors)
            self.assertEqual(result["test_errors"], test_errors)

    def test_test_labels_cannot_enter_selection_or_change_predictions(self):
        for problem, result in self.results.items():
            training = solution.load(result["training_year"])
            changed = [replace(r, label="D" if r.label == "R" else "R")
                       for r in solution.load(result["test_year"])]
            selection = (result["selected_k"], result["all_minimizing_k"], result["loocv_errors_by_k"])
            with patch.object(solution, "select_k", return_value=selection) as select:
                altered = solution.analyze(problem, training, changed, result["training_year"], result["test_year"])
            select.assert_called_once_with(training)
            self.assertEqual(altered["test_predictions"], result["test_predictions"])
            self.assertEqual(altered["selected_k"], result["selected_k"])
            self.assertEqual(altered["test_errors"] + result["test_errors"], 51)


if __name__ == "__main__":
    unittest.main()
