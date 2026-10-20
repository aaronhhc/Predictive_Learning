# Homework 1

Name: 黃竑喆  
Student ID: 61547048S  
Repository: [https://github.com/aaronhhc/Predictive_Learning/tree/main/hw1](https://github.com/aaronhhc/Predictive_Learning/tree/main/hw1)

Topics: Risk Minimization + Model Selection

## Problem 2.7

The task is to classify the presidential election outcome (Republican or Democrat) using obesity percentage as the only predictor. Each dataset has 51 observations (50 states and the District of Columbia). I trained on the 2004 data and tested on the 2000 data.

I used scikit-learn's `KNeighborsClassifier` with default settings and `LeaveOneOut` on the 2004 data for k = 1,…,50. The resampling error is the fraction of misclassified held-out points. If several k values tie for the minimum, I took the smallest one. The chosen model was then fitted to all 2004 samples and evaluated on the 2000 data.

| Training → evaluation | Selected k | Resampling error (LOOCV) | Test error |
|---|---:|---:|---:|
| 2004 → 2000 | **7** | **14/51 = 27.45%** | **27/51 = 52.94%** |

The minimum LOOCV error is 14/51 = 27.45%, so k = 7 is selected. After fitting the model on all 2004 samples, the test error on the 2000 data is 27/51 = 52.94%. The larger test error suggests that obesity percentage alone does not generalize well across the two election years. (The set of tied k values can depend on how equal-distance neighbors are ordered, but k = 7 is unchanged.)

## Problem 2.8

I repeated the procedure with the years reversed: LOOCV on the 2000 data to select k, then testing on the 2004 data.

| Training → evaluation | Selected k | Resampling error (LOOCV) | Test error |
|---|---:|---:|---:|
| 2000 → 2004 | **16** | **19/51 = 37.25%** | **19/51 = 37.25%** |

The minimum LOOCV error is 19/51 = 37.25%, so k = 16 is selected. The test error on the 2004 data is also 19/51 = 37.25%. Compared with Problem 2.7, the LOOCV error is higher but the test error is lower, so training on 2000 and testing on 2004 gives the better result. Obesity percentage alone remains a weak predictor.

## Problem 2.11

The homework gives the data-generating process but not the data, so I generated one n = 10 sample with random seed 20261006 and used it in both Problems 2.11 and 2.12.

The data were generated as

$$
x\sim\operatorname{Uniform}[0,1],\qquad
y=x^2+0.1x+\varepsilon,\qquad
\varepsilon\sim N(0,0.25).
$$

The noise variance is 0.25 (standard deviation 0.5).

I used the Schwartz criterion in the form

$$
\widehat R=r(p,n)R_{\mathrm{emp}},\qquad
r(p,n)=1+\frac{p}{1-p}\ln(n),\qquad
p=\frac{\mathrm{DoF}}{n},
$$

where

$$
R_{\mathrm{emp}}=\frac{1}{n}\sum_{j=1}^{n}\bigl(y_j-\widehat f_m(x_j)\bigr)^2.
$$

Both model families have DoF = m + 1. For n = 10, the condition DoF < n gives candidates m = 0,…,8. Each model is fitted by least squares, and the m with the smallest estimated risk is selected. Table entries are rounded to six decimal places.

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

The selected order is **m = 4** (DoF = 5). Although the training MSE keeps decreasing, the Schwartz penalty increases with model complexity, giving the minimum estimated risk at m = 4.

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

The selected degree is **m = 7** (DoF = 8). Degree 8 has a lower training MSE, but its larger penalty gives a higher estimated risk.

### Conceptual question

No. The Schwartz criterion selects the model order within each family, but does not directly compare their predictive accuracy. A held-out evaluation is needed, which is done in Problem 2.12.

## Problem 2.12

I compared the two families with 5-fold cross-validation on the same ten observations. Both families use the same folds (random seed 212), with two held-out samples per fold; the sample IDs index the data from Problem 2.11.

In each fold, the other eight samples form the training set. I fitted m = 0,…,6 (so DoF = m + 1 < 8, with n = 8), selected m by the Schwartz criterion using only these training samples, and predicted the two held-out samples. The ten squared errors are pooled:

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

The algebraic models have a much smaller 5-fold CV MSE for this dataset. However, only 10 samples are used and the trigonometric error is strongly affected by fold 2, so the comparison should be interpreted cautiously.
