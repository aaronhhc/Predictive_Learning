# Homework 1 — Odd-k sensitivity analysis

This supplements the primary analysis without changing it. Both datasets contain 50 states plus the District of Columbia (51 observations).

The sensitivity analysis restricts the candidates to odd k = 1, 3, …, 49, eliminating class-vote ties in binary, unweighted kNN. It retains the primary implementation's distance-tie ordering by jurisdiction code and its convention of selecting the smallest k among equal minimum LOOCV errors. Selection uses only the training year; test-year labels are used only for evaluation. These are implementation choices, not assignment requirements.

| Problem | Training → test | Analysis | All minimizing k values | Selected k | LOOCV error | Test error |
|---|---|---|---|---:|---:|---:|
| 2.7 | 2004 → 2000 | Primary: all k | 2, 3, 5, 12, 17 | 2 | 15/51 (29.41%) | 27/51 (52.94%) |
| 2.7 | 2004 → 2000 | Sensitivity: odd k | 3, 5, 17 | 3 | 15/51 (29.41%) | 29/51 (56.86%) |
| 2.8 | 2000 → 2004 | Primary: all k | 8 | 8 | 15/51 (29.41%) | 20/51 (39.22%) |
| 2.8 | 2000 → 2004 | Sensitivity: odd k | 7, 25, 27, 29 | 7 | 19/51 (37.25%) | 22/51 (43.14%) |

Problem 2.7 changes from k = 2 to k = 3, with unchanged minimum LOOCV error and two additional test errors (an increase of 3.92 percentage points). Problem 2.8 changes from k = 8 to k = 7, with four additional LOOCV errors (7.84 percentage points) and two additional test errors (3.92 percentage points). The odd-k minimum is nonunique in both problems, so the smallest-k convention still matters.

The numerical results show some sensitivity to k/tie conventions, particularly for Problem 2.8. The substantive conclusion remains unchanged: obesity alone provides poor cross-year election prediction in these experiments. In both directions, test error exceeds the selected LOOCV error, and neither variant improves on always predicting the training majority class, R (test errors of 21/51 for 2.7 and 19/51 for 2.8).

Restricting the candidate range to odd k removes vote ties but also changes which models are eligible. This comparison therefore does not isolate the effect of replacing one even-k vote-tie rule with another. It also does not evaluate alternative choices among tied minimum-error k values. No test errors were used to choose among those minima.

Disclosure verified: `classification_report.md` explicitly introduces the conventions with “Implementation choices, not assignment requirements,” then specifies fitting-set majority for vote ties (D if the fitting set itself ties) and smallest k among tied LOOCV minima. No modification to that report was needed.

Verification reused the saved primary LOOCV scores to check every odd-k minimum and independently checked the 102 selected odd-k test predictions by direct majority vote. SHA-256 checks confirmed that the primary report, all primary result files, and the original PDF/CSV files remain unchanged. The machine-readable comparison is saved separately in `results/sensitivity_comparison.csv`.

Problems 2.11 and 2.12 remain pending the actual Example 2.6 observations and the verified course/textbook Schwarz criterion.
