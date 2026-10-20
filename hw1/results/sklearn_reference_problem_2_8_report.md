# Independent Problem 2.8 reference and internal comparison

Before changing the final report, all 2,550 fits were independently computed
with KNeighborsClassifier(n_neighbors=k), all other defaults, and LeaveOneOut.
Training is 2000; test is 2004. Both original CSVs retain all 51 observations
and their original order. Scikit-learn version: 1.9.1. Class ordering: D, R.
The 2000 class counts are D: 21 and R: 30.

All minimizing k values: 16, 24, 25, 26, 27, 28.
Minimum LOOCV error: 19/51 = 37.25%.
The smallest-k convention selects 16; its test error is 19/51 = 37.25%.
Test errors at the other minimizing k values do not influence this selection.

The old custom result selected k=8, with LOOCV 15/51 and test error 20/51.
Under sklearn, k=8 has 25/51 LOOCV mistakes. Twelve fold predictions change:
eleven previously correct predictions become mistakes, and one old mistake
is corrected, giving a net increase of ten. Vote ties use D under sklearn
rather than the fitting majority R; neighbor boundaries can also differ.

The first prediction disagreement in ascending k and original row order is
k=1, held-out Illinois (CSV row 14), obesity 20.4%, true label D. The custom
exact-distance/code ordering selects Indiana (20.5%, R), whereas sklearn
selects Pennsylvania (20.3%, D). Their mathematical distances are both 0.1
percentage points, but float64 absolute distances are 0.10000000000000142
and 0.09999999999999787, respectively. This disagreement is caused by
floating-point distance behavior at an exact-distance boundary tie; no vote
tie is possible at k=1.

The custom policy was independently reconstructed solely for this diagnostic,
without importing or calling its prediction function. Its counts matched all
50 originally saved Problem 2.8 LOOCV counts. The final solver uses sklearn
exclusively, and its 50 scores and selected-model predictions match this
independent reference. Full fold and neighbor evidence is saved in the
separately named CSV and JSON diagnostic files.
