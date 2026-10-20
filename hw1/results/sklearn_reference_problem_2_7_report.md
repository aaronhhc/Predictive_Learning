# Independent reference check: Homework 1 Problem 2.7

The original supplied CSVs were read in their original row order, with 2004
training data, 2000 test data, and obesity percentage as the sole predictor.
Both datasets contain all 51 jurisdictions, including DC. Each of the 2,550
LOOCV fits used exactly 50 observations and predicted the excluded observation.
The estimator was `KNeighborsClassifier(n_neighbors=k)` with all other settings
left at their defaults, including uniform weights. Folds came from `LeaveOneOut`.
Percentages were parsed directly as float64 percentage-point values.

Environment: scikit-learn **1.9.1**, NumPy **2.5.3**. Class ordering is
**[D, R]**. Training class counts are **D: 19, R: 32**.

All minimum-error k values are **7, 9, 20, 22**. Each gives **14/51 = 27.450980%**
LOOCV error. No single k has been selected from this tie.

| k | sklearn LOOCV mistakes | sklearn error | Existing custom mistakes | Custom error |
|---:|---:|---:|---:|---:|
| 2 | 19 | 37.254902% | 15 | 29.411765% |
| 3 | 16 | 31.372549% | 15 | 29.411765% |
| 5 | 15 | 29.411765% | 15 | 29.411765% |
| 12 | 20 | 39.215686% | 15 | 29.411765% |
| 17 | 15 | 29.411765% | 15 | 29.411765% |
| 20 | 14 | 27.450980% | 19 | 37.254902% |
| 22 | 14 | 27.450980% | 19 | 37.254902% |

After fitting each minimizing k on all 51 observations from 2004:

| k | 2000 test mistakes | Test error |
|---:|---:|---:|
| 7 | 27/51 | 52.941176% |
| 9 | 25/51 | 49.019608% |
| 20 | 28/51 | 54.901961% |
| 22 | 28/51 | 54.901961% |

## First disagreement

Searching k in ascending order, then held-out samples in original CSV order,
there are no disagreements at k=1. The first is **k=2, Arizona**, zero-based
sample index 2, CSV row 3. Arizona's obesity is 20.3%, and its supplied label is R.
Both methods select New Jersey (20.3%, D, distance 0) and New Mexico
(20.5%, R, distance 0.2 percentage points). The votes tie 1 D to 1 R.
Scikit-learn predicts D, the first class in its ordering. The custom policy
predicts R, the majority of the 50-observation fitting set (31 R, 19 D).

This first disagreement is caused exactly by the **class-vote tie rule and class
ordering**. An equal-distance boundary tie also exists with Wyoming, but both
methods choose New Mexico here, so it does not cause this disagreement.

## Exactly why k=20 and k=22 attain the minimum

For each k there are exactly five changed predictions versus the custom policy,
all changing R to D for a truly D held-out sample. No correct custom prediction
becomes incorrect. Thus each error count drops from 19 to 14.

At **k=20**, Delaware, Massachusetts, Minnesota, and Rhode Island have the same
neighbors under both methods, with 10 D and 10 R votes. Scikit-learn's D tie
rule corrects these four predictions. Wisconsin is the fifth correction:
its custom neighbors have 10 D and 10 R, whereas sklearn's have 11 D and 9 R.
Wisconsin's obesity is 21.9%; Alaska (23.5%, R) and New Jersey (20.3%, D)
are both exactly 1.6 percentage points away. Exact-distance sorting by code
includes Alaska; sklearn includes New Jersey. In float64 their absolute
distances are respectively `1.6000000000000014` and `1.5999999999999979`.
Thus the fifth correction includes a **floating-point distance/boundary
neighbor difference**, in addition to the custom policy's R vote fallback.

At **k=22**, Delaware, Maryland, Minnesota, Washington, and Wisconsin each
have identical neighbor sets under both methods, with 11 D and 11 R votes.
All five corrections are directly due to the D versus R vote tie rules.

## Comparison and preservation

The existing custom minimum is 15/51 (29.411765%), attained at
**2, 3, 5, 12, 17**. Its previously selected k=2 has test error 27/51.
The comparison independently reconstructs its documented exact-distance,
jurisdiction-code, and training-majority rules; it never imports or calls the
custom prediction function. This reconstruction matches all 50 existing saved
Problem 2.7 LOOCV mistake counts. Across all k and folds there are 147 prediction
disagreements. Neighbor ordering and float representation also affect some
predictions, including at odd k where vote ties cannot occur.

The main CSV contains mistakes and error rates for **every k=1,...,50**.
The fold CSV contains all 2,550 predictions, and the differences JSON contains
neighbor-level evidence for all disagreements. The summary JSON records the
environment, class counts, results, first disagreement, and original file hashes.
All pre-existing report, PDF, analysis, input, and result files passed the
before/after SHA-256 preservation check.

Reproduce with the separate temporary environment created for this check:

```sh
/private/tmp/hw1-sklearn-reference-env/bin/python sklearn_reference_check.py
```

For another environment, use scikit-learn 1.9.1 and NumPy 2.5.3 to reproduce
this reference's versions. Default neighbor boundary behavior can depend on
library version and original input ordering when distances tie.
