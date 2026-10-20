# Homework 1

Name: 黃竑喆  
Student ID: 61547048S

Topics: Risk Minimization + Model Selection

## Problem 2.7

The task is binary classification of presidential election outcomes (Republican or Democrat) using obesity percentage as the sole predictor. Each supplied dataset contains the 50 states plus the District of Columbia, giving 51 observations. The 2004 data are used for training and the 2000 data for evaluation; the supplied labels and original row order are retained.

The analysis uses scikit-learn's standard `KNeighborsClassifier` with default uniform weighting and all other estimator settings at their defaults (scikit-learn 1.9.1). `LeaveOneOut` evaluates k = 1,…,50 on the training year: each classifier is fitted on exactly 50 observations and predicts the one held-out observation. Resampling error is the fraction of incorrect predictions. The selected classifier is then fitted to all 51 training observations and evaluated on the other year. Test-year labels are never used for model selection.

If multiple k values achieve the minimum LOOCV error, the smallest minimizing k is selected as an **implementation convention**.

| Training → evaluation | Selected k | Resampling error (LOOCV) | Test error |
|---|---:|---:|---:|
| 2004 → 2000 | **7** | **14/51 = 27.45%** | **27/51 = 52.94%** |

The LOOCV minimum is attained at **k = 7, 9, 20, and 22**, so k = 7 is selected by the stated convention. The substantially higher test error indicates poor cross-year generalization. Identical obesity values sometimes have opposite voting labels, limiting classification with this single predictor. Changes in obesity distributions and voting outcomes also make a stable relationship across years questionable. LOOCV evaluates prediction within 2004, whereas the test evaluates transfer to 2000. These datasets revisit the same jurisdictions, so this is cross-year evaluation rather than evaluation on new independent jurisdictions.

## Problem 2.8

The same scikit-learn classifier, uniform weighting, LeaveOneOut procedure, candidate range, and smallest-k convention are applied with the years reversed: training uses 2000 and evaluation uses 2004. All k = 1,…,50 are recomputed, and model selection uses only the 2000 observations and labels.

| Training → evaluation | Selected k | Resampling error (LOOCV) | Test error |
|---|---:|---:|---:|
| 2000 → 2004 | **16** | **19/51 = 37.25%** | **19/51 = 37.25%** |

The LOOCV minimum is attained at **k = 16, 24, 25, 26, 27, and 28**, so k = 16 is selected. Its minimum resampling error is higher than that of Problem 2.7, while its test error is lower and equals its resampling error. For context, always predicting the training majority class, Republican, yields test errors of 41.18% in Problem 2.7 and 37.25% here. Thus the selected kNN model is worse than that baseline in Problem 2.7 and matches it in Problem 2.8. These results provide limited evidence for cross-year prediction from obesity alone. The minimum LOOCV error is used for model selection and is not an independent post-selection estimate.

## Problem 2.11

The numerical realization used in textbook Example 2.6 was not provided in the available course materials. Therefore, a reproducible realization with random seed 20261006 was generated from the data-generating process explicitly specified in Homework 1, and the same realization is reused in Problems 2.11 and 2.12.

The ten observations follow

$$
x\sim\operatorname{Uniform}[0,1],\qquad
y=x^2+0.1x+\varepsilon,\qquad
\varepsilon\sim N(0,0.25).
$$

The noise variance is 0.25 and its standard deviation is 0.5.

The course-specific analytic Schwartz criterion is

$$
\widehat R=r(p,n)R_{\mathrm{emp}},\qquad
r(p,n)=1+\frac{p}{1-p}\ln(n),\qquad
p=\frac{\mathrm{DoF}}{n},
$$

where

$$
R_{\mathrm{emp}}=\frac{1}{n}\sum_{j=1}^{n}\bigl(y_j-\widehat f_m(x_j)\bigr)^2.
$$

Both model families have DoF = m + 1. For n = 10, the condition DoF < n gives candidates m = 0,…,8. Each candidate is fitted by numerically stable least squares, and the model minimizing the Schwartz-estimated risk is selected. Table entries below are rounded to six decimal places.

### Trigonometric polynomial

The model is

$$
f_m(x)=w_0+\sum_{i=1}^{m}w_i\cos(2\pi i x).
$$

| m | DoF | Training MSE R_emp | Multiplier r(p,10) | Estimated risk R_hat |
|---:|---:|---:|---:|---:|
| 0 | 1 | 0.354726 | 1.255843 | 0.445480 |
| 1 | 2 | 0.284175 | 1.575646 | 0.447759 |
| 2 | 3 | 0.151407 | 1.986822 | 0.300818 |
| 3 | 4 | 0.147274 | 2.535057 | 0.373349 |
| **4** | **5** | **0.058441** | **3.302585** | **0.193007** |
| 5 | 6 | 0.047292 | 4.453878 | 0.210635 |
| 6 | 7 | 0.039081 | 6.372699 | 0.249053 |
| 7 | 8 | 0.036984 | 10.210340 | 0.377618 |
| 8 | 9 | 0.019128 | 21.723266 | 0.415520 |

The selected order is **m = 4**, with DoF = 5. Although training MSE continues to decrease, the increasing complexity multiplier raises the estimated risk beyond this order.

### Algebraic polynomial

The model is

$$
f_m(x)=w_0+w_1x+\cdots+w_mx^m.
$$

| m | DoF | Training MSE R_emp | Multiplier r(p,10) | Estimated risk R_hat |
|---:|---:|---:|---:|---:|
| 0 | 1 | 0.354726 | 1.255843 | 0.445480 |
| 1 | 2 | 0.132197 | 1.575646 | 0.208295 |
| 2 | 3 | 0.132006 | 1.986822 | 0.262273 |
| 3 | 4 | 0.131412 | 2.535057 | 0.333136 |
| 4 | 5 | 0.117993 | 3.302585 | 0.389682 |
| 5 | 6 | 0.038780 | 4.453878 | 0.172722 |
| 6 | 7 | 0.032091 | 6.372699 | 0.204505 |
| **7** | **8** | **0.016643** | **10.210340** | **0.169933** |
| 8 | 9 | 0.014709 | 21.723266 | 0.319528 |

The selected degree is **m = 7**, with DoF = 8. Degree 8 reduces training error further, but its larger multiplier produces a higher estimated risk.

### Conceptual question

**The two separate Schwartz minima do not by themselves establish which model family has better predictive accuracy.** They select complexity within each family using estimated risk rather than independently observed prediction errors. Predictive comparison requires the held-out evaluation in Problem 2.12.

## Problem 2.12

Five-fold cross-validation compares the two model families using the same ten observations. Both families use **identical folds**, with two held-out observations per fold. The fold partition is fixed using random seed 212; Sample IDs in the table index the simulated realization used in Problems 2.11 and 2.12.

For each outer fold, the remaining eight observations form the training set. Models with m = 0,…,6 are fitted and selected by Schwartz using **only those training observations**, with n = 8 and DoF = m + 1 < 8. The selected model predicts the two held-out observations, and their squared prediction errors are recorded. **Held-out data are never used for model selection within their fold.** The ten held-out squared errors are pooled to calculate

$$
\operatorname{MSE}_{\mathrm{CV}}
=
\frac{1}{10}\sum_{j=1}^{10}
\bigl(y_j-\widehat f_{-\operatorname{fold}(j)}(x_j)\bigr)^2.
$$

| Fold | Held-out sample IDs | Trig. selected m | Trig. fold MSE | Alg. selected m | Alg. fold MSE |
|---:|---|---:|---:|---:|---:|
| 1 | 3, 1 | 6 | 1.555883 | 5 | 0.308201 |
| 2 | 7, 6 | 6 | 111.460273 | 6 | 0.829983 |
| 3 | 9, 5 | 6 | 0.238543 | 5 | 0.546663 |
| 4 | 8, 0 | 4 | 0.046822 | 1 | 0.119016 |
| 5 | 2, 4 | 2 | 0.860503 | 1 | 0.144008 |

| Model family | Five-fold CV MSE |
|---|---:|
| Trigonometric | **22.8324047943** |
| Algebraic | **0.3895744061** |

**Algebraic models perform better for this simulated realization and this fold partition.** However, n = 10 is extremely small, and the trigonometric error is dominated by fold 2. The algebraic full-data fit is also unstable near x = 0, where this realization has no observations. Consequently, these results do not establish universal superiority over the entire input domain or across other random realizations.

## Final concise conclusion

Model selection balances training fit against complexity, but neither a low training error nor a minimum estimated risk guarantees predictive accuracy. Resampling guides complexity selection, while test error and held-out prediction errors assess generalization. The classification examples show that within-year resampling can underestimate cross-year error. The regression comparison shows that complexity control and predictive evaluation serve distinct purposes: Schwartz selects model order within each family, and cross-validation compares the resulting prediction procedures, subject to the limitations of a very small sample.
