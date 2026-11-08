## Table 1. Data summary
| method | period | rows | cells | pct_present |
|---|---|---|---|---|
| public | other | 511 | 100 | 100 |
| public | test | 144459 | 1614 | 100 |
| public | train | 280777 | 1102 | 100 |
| survey | other | 126741 | 1687 | 9.3 |
| survey | test | 106102 | 3157 | 19.4 |
| survey | train | 272594 | 3531 | 11.8 |
| analysis | test cells: all | 1917 | 1917 | 49.1 |
| analysis | test cells: reported_cells | 771 | 771 | 74.2 |
| analysis | test cells: zero_report_cells | 1146 | 1146 | 32.2 |
| analysis | test cells: core_states | 931 | 931 | 57.4 |
| analysis | test cells: transfer_states | 986 | 986 | 41.3 |
| analysis | training positive cells | 280775 | 1100 | 100 |
| analysis | accessible-area cells (M) |  | 3266 |  |

## AUC by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.799 | 0.832 | 0.66 | 0.907 | 0.819 |
| - | Baseline: report count | 0.744 | 0.836 | 0.5 | 0.887 | 0.587 |
| MaxEnt-style logistic | Effort covariate held constant | 0.746 | 0.675 | 0.635 | 0.744 | 0.767 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.78 | 0.698 | 0.694 | 0.764 | 0.813 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.743 | 0.612 | 0.662 | 0.68 | 0.802 |
| MaxEnt-style logistic | KDE-matched background | 0.729 | 0.787 | 0.602 | 0.863 | 0.646 |
| MaxEnt-style logistic | Random background | 0.784 | 0.754 | 0.67 | 0.82 | 0.783 |
| MaxEnt-style logistic | Spatial thinning | 0.671 | 0.576 | 0.587 | 0.576 | 0.725 |
| Random forest | Effort covariate held constant | 0.735 | 0.699 | 0.552 | 0.833 | 0.732 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.781 | 0.735 | 0.665 | 0.806 | 0.798 |
| Random forest | Proposed + inverse-propensity weights | 0.753 | 0.672 | 0.645 | 0.735 | 0.791 |
| Random forest | KDE-matched background | 0.687 | 0.803 | 0.342 | 0.879 | 0.445 |
| Random forest | Random background | 0.754 | 0.746 | 0.573 | 0.853 | 0.738 |
| Random forest | Spatial thinning | 0.648 | 0.377 | 0.549 | 0.518 | 0.703 |

## Average precision by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.815 | 0.921 | 0.48 | 0.914 | 0.792 |
| - | Baseline: report count | 0.753 | 0.922 | 0.322 | 0.904 | 0.515 |
| MaxEnt-style logistic | Effort covariate held constant | 0.735 | 0.839 | 0.44 | 0.783 | 0.7 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.765 | 0.85 | 0.491 | 0.803 | 0.784 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.69 | 0.778 | 0.417 | 0.703 | 0.747 |
| MaxEnt-style logistic | KDE-matched background | 0.644 | 0.884 | 0.377 | 0.869 | 0.483 |
| MaxEnt-style logistic | Random background | 0.782 | 0.876 | 0.505 | 0.841 | 0.728 |
| MaxEnt-style logistic | Spatial thinning | 0.607 | 0.793 | 0.349 | 0.619 | 0.594 |
| Random forest | Effort covariate held constant | 0.74 | 0.848 | 0.331 | 0.836 | 0.675 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.767 | 0.861 | 0.481 | 0.81 | 0.781 |
| Random forest | Proposed + inverse-propensity weights | 0.723 | 0.832 | 0.43 | 0.748 | 0.772 |
| Random forest | KDE-matched background | 0.75 | 0.904 | 0.252 | 0.89 | 0.465 |
| Random forest | Random background | 0.767 | 0.878 | 0.353 | 0.865 | 0.686 |
| Random forest | Spatial thinning | 0.573 | 0.662 | 0.334 | 0.554 | 0.588 |

## False-positive rate at 20% alert budget (lower is better) by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.057 | 0.276 | 0.001 | 0.141 | 0.0 |
| - | Baseline: report count | 0.087 | 0.427 | 0.0 | 0.214 | 0.0 |
| MaxEnt-style logistic | Effort covariate held constant | 0.116 | 0.362 | 0.053 | 0.262 | 0.016 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.096 | 0.352 | 0.031 | 0.227 | 0.007 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.13 | 0.387 | 0.064 | 0.312 | 0.005 |
| MaxEnt-style logistic | KDE-matched background | 0.106 | 0.111 | 0.104 | 0.053 | 0.142 |
| MaxEnt-style logistic | Random background | 0.082 | 0.286 | 0.03 | 0.174 | 0.019 |
| MaxEnt-style logistic | Spatial thinning | 0.164 | 0.317 | 0.125 | 0.3 | 0.071 |
| Random forest | Effort covariate held constant | 0.092 | 0.432 | 0.005 | 0.224 | 0.002 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.091 | 0.286 | 0.041 | 0.222 | 0.002 |
| Random forest | Proposed + inverse-propensity weights | 0.106 | 0.332 | 0.048 | 0.249 | 0.007 |
| Random forest | KDE-matched background | 0.076 | 0.327 | 0.012 | 0.161 | 0.017 |
| Random forest | Random background | 0.089 | 0.427 | 0.003 | 0.212 | 0.005 |
| Random forest | Spatial thinning | 0.208 | 0.613 | 0.104 | 0.413 | 0.067 |

## Sensitivity at 20% alert budget by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.523 | 0.837 | 0.035 | 0.833 | 0.115 |
| - | Baseline: report count | 0.548 | 0.902 | 0.0 | 0.884 | 0.108 |
| MaxEnt-style logistic | Effort covariate held constant | 0.416 | 0.619 | 0.1 | 0.614 | 0.155 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.437 | 0.657 | 0.095 | 0.652 | 0.155 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.389 | 0.593 | 0.073 | 0.594 | 0.12 |
| MaxEnt-style logistic | KDE-matched background | 0.29 | 0.404 | 0.114 | 0.397 | 0.15 |
| MaxEnt-style logistic | Random background | 0.465 | 0.684 | 0.127 | 0.68 | 0.184 |
| MaxEnt-style logistic | Spatial thinning | 0.305 | 0.437 | 0.1 | 0.412 | 0.165 |
| Random forest | Effort covariate held constant | 0.479 | 0.781 | 0.011 | 0.805 | 0.052 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.463 | 0.694 | 0.106 | 0.697 | 0.157 |
| Random forest | Proposed + inverse-propensity weights | 0.425 | 0.631 | 0.106 | 0.635 | 0.15 |
| Random forest | KDE-matched background | 0.484 | 0.795 | 0.0 | 0.798 | 0.071 |
| Random forest | Random background | 0.487 | 0.799 | 0.003 | 0.798 | 0.079 |
| Random forest | Spatial thinning | 0.318 | 0.476 | 0.073 | 0.429 | 0.172 |

## Change in AUC vs random background (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | -0.038 [-0.052, -0.026] | -0.079 [-0.113, -0.052] | -0.036 [-0.051, -0.022] | -0.077 [-0.108, -0.051] | -0.016 [-0.027, -0.007] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | -0.004 [-0.021, +0.015] | -0.056 [-0.088, -0.023] | +0.023 [+0.003, +0.044] | -0.057 [-0.086, -0.032] | +0.030 [+0.012, +0.048] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | -0.042 [-0.065, -0.017] | -0.142 [-0.203, -0.087] | -0.008 [-0.037, +0.016] | -0.141 [-0.195, -0.093] | +0.018 [+0.001, +0.035] |
| MaxEnt-style logistic | KDE-matched background | -0.055 [-0.094, -0.019] | +0.032 [+0.008, +0.061] | -0.068 [-0.124, -0.025] | +0.042 [+0.018, +0.082] | -0.137 [-0.200, -0.093] |
| MaxEnt-style logistic | Spatial thinning | -0.113 [-0.148, -0.081] | -0.178 [-0.254, -0.116] | -0.083 [-0.113, -0.055] | -0.244 [-0.336, -0.157] | -0.058 [-0.080, -0.039] |
| Random forest | Effort covariate held constant | -0.019 [-0.031, -0.006] | -0.047 [-0.098, +0.002] | -0.021 [-0.037, -0.005] | -0.020 [-0.047, +0.004] | -0.006 [-0.020, +0.006] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.027 [+0.003, +0.054] | -0.011 [-0.082, +0.058] | +0.092 [+0.066, +0.123] | -0.047 [-0.118, -0.001] | +0.060 [+0.036, +0.085] |
| Random forest | Proposed + inverse-propensity weights | -0.001 [-0.032, +0.029] | -0.074 [-0.163, +0.002] | +0.072 [+0.048, +0.100] | -0.118 [-0.202, -0.055] | +0.054 [+0.028, +0.078] |
| Random forest | KDE-matched background | -0.066 [-0.097, -0.036] | +0.057 [+0.026, +0.088] | -0.231 [-0.297, -0.158] | +0.026 [+0.011, +0.050] | -0.293 [-0.364, -0.219] |
| Random forest | Spatial thinning | -0.106 [-0.147, -0.074] | -0.369 [-0.452, -0.276] | -0.024 [-0.045, -0.003] | -0.335 [-0.408, -0.273] | -0.035 [-0.055, -0.016] |

## Change in FPR vs random background (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | +0.034 [+0.010, +0.073] | +0.075 [+0.005, +0.164] | +0.023 [+0.001, +0.050] | +0.088 [+0.023, +0.173] | -0.003 [-0.008, +0.000] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | +0.014 [-0.005, +0.036] | +0.065 [+0.015, +0.115] | +0.001 [-0.017, +0.021] | +0.053 [+0.010, +0.095] | -0.012 [-0.029, +0.000] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | +0.048 [+0.015, +0.089] | +0.101 [+0.028, +0.197] | +0.035 [-0.001, +0.070] | +0.139 [+0.058, +0.237] | -0.014 [-0.032, +0.000] |
| MaxEnt-style logistic | KDE-matched background | +0.024 [-0.030, +0.067] | -0.176 [-0.268, -0.075] | +0.075 [+0.032, +0.123] | -0.121 [-0.189, -0.052] | +0.123 [+0.080, +0.183] |
| MaxEnt-style logistic | Spatial thinning | +0.082 [+0.035, +0.131] | +0.030 [-0.094, +0.174] | +0.095 [+0.050, +0.146] | +0.126 [+0.034, +0.265] | +0.052 [+0.026, +0.079] |
| Random forest | Effort covariate held constant | +0.003 [-0.013, +0.022] | +0.005 [-0.063, +0.076] | +0.003 [-0.003, +0.009] | +0.013 [-0.030, +0.057] | -0.003 [-0.010, +0.000] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.002 [-0.030, +0.041] | -0.141 [-0.233, -0.018] | +0.039 [+0.014, +0.066] | +0.010 [-0.068, +0.095] | -0.003 [-0.013, +0.004] |
| Random forest | Proposed + inverse-propensity weights | +0.016 [-0.023, +0.061] | -0.095 [-0.207, +0.025] | +0.045 [+0.019, +0.071] | +0.038 [-0.056, +0.141] | +0.002 [-0.004, +0.008] |
| Random forest | KDE-matched background | -0.013 [-0.029, +0.005] | -0.101 [-0.153, -0.047] | +0.009 [-0.001, +0.024] | -0.050 [-0.082, -0.018] | +0.012 [-0.002, +0.031] |
| Random forest | Spatial thinning | +0.119 [+0.077, +0.161] | +0.186 [+0.044, +0.316] | +0.102 [+0.070, +0.137] | +0.202 [+0.124, +0.286] | +0.062 [+0.034, +0.096] |

## Change in AUC vs report-density (KDE) baseline (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | -0.052 [-0.090, -0.018] | -0.157 [-0.228, -0.093] | -0.026 [-0.070, +0.023] | -0.164 [-0.260, -0.094] | -0.052 [-0.095, -0.018] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | -0.018 [-0.048, +0.010] | -0.134 [-0.188, -0.075] | +0.034 [-0.007, +0.079] | -0.144 [-0.237, -0.081] | -0.006 [-0.032, +0.019] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | -0.056 [-0.095, -0.022] | -0.220 [-0.290, -0.146] | +0.002 [-0.037, +0.048] | -0.228 [-0.334, -0.143] | -0.018 [-0.043, +0.007] |
| MaxEnt-style logistic | KDE-matched background | -0.070 [-0.117, -0.021] | -0.045 [-0.086, -0.002] | -0.058 [-0.126, +0.015] | -0.045 [-0.083, -0.021] | -0.173 [-0.242, -0.110] |
| MaxEnt-style logistic | Random background | -0.015 [-0.044, +0.015] | -0.078 [-0.126, -0.025] | +0.010 [-0.036, +0.058] | -0.087 [-0.153, -0.042] | -0.036 [-0.070, -0.004] |
| MaxEnt-style logistic | Spatial thinning | -0.128 [-0.183, -0.084] | -0.256 [-0.365, -0.160] | -0.073 [-0.116, -0.025] | -0.331 [-0.464, -0.243] | -0.094 [-0.141, -0.055] |
| Random forest | Effort covariate held constant | -0.064 [-0.087, -0.048] | -0.133 [-0.197, -0.081] | -0.108 [-0.142, -0.069] | -0.075 [-0.104, -0.049] | -0.087 [-0.117, -0.056] |
| Random forest | Effort-weighted constrained PA (proposed) | -0.018 [-0.045, +0.003] | -0.096 [-0.159, -0.041] | +0.005 [-0.033, +0.038] | -0.102 [-0.170, -0.054] | -0.021 [-0.052, +0.008] |
| Random forest | Proposed + inverse-propensity weights | -0.046 [-0.077, -0.019] | -0.160 [-0.240, -0.092] | -0.015 [-0.049, +0.017] | -0.172 [-0.257, -0.109] | -0.028 [-0.058, -0.000] |
| Random forest | KDE-matched background | -0.112 [-0.153, -0.070] | -0.029 [-0.056, +0.003] | -0.318 [-0.392, -0.233] | -0.028 [-0.049, -0.009] | -0.375 [-0.460, -0.301] |
| Random forest | Random background | -0.045 [-0.060, -0.030] | -0.086 [-0.121, -0.052] | -0.087 [-0.121, -0.052] | -0.054 [-0.079, -0.029] | -0.082 [-0.112, -0.054] |
| Random forest | Spatial thinning | -0.151 [-0.188, -0.113] | -0.454 [-0.543, -0.354] | -0.111 [-0.154, -0.075] | -0.390 [-0.450, -0.313] | -0.116 [-0.151, -0.082] |

## Change in FPR vs report-density (KDE) baseline (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | +0.058 [+0.013, +0.119] | +0.085 [-0.014, +0.215] | +0.051 [+0.021, +0.083] | +0.121 [+0.036, +0.244] | +0.016 [+0.003, +0.031] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | +0.039 [+0.000, +0.090] | +0.075 [-0.017, +0.172] | +0.030 [+0.010, +0.057] | +0.086 [+0.007, +0.187] | +0.007 [+0.000, +0.017] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | +0.073 [+0.021, +0.134] | +0.111 [+0.011, +0.231] | +0.063 [+0.032, +0.100] | +0.171 [+0.041, +0.282] | +0.005 [+0.000, +0.016] |
| MaxEnt-style logistic | KDE-matched background | +0.048 [+0.011, +0.085] | -0.166 [-0.251, -0.076] | +0.103 [+0.069, +0.146] | -0.088 [-0.137, -0.040] | +0.142 [+0.086, +0.197] |
| MaxEnt-style logistic | Random background | +0.025 [-0.005, +0.056] | +0.010 [-0.068, +0.102] | +0.028 [+0.010, +0.049] | +0.033 [-0.027, +0.113] | +0.019 [+0.004, +0.037] |
| MaxEnt-style logistic | Spatial thinning | +0.107 [+0.052, +0.168] | +0.040 [-0.074, +0.167] | +0.124 [+0.079, +0.176] | +0.159 [+0.036, +0.264] | +0.071 [+0.042, +0.103] |
| Random forest | Effort covariate held constant | +0.035 [+0.019, +0.052] | +0.156 [+0.101, +0.227] | +0.004 [-0.001, +0.010] | +0.083 [+0.052, +0.131] | +0.002 [+0.000, +0.005] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.034 [-0.003, +0.072] | +0.010 [-0.090, +0.116] | +0.040 [+0.017, +0.064] | +0.081 [+0.017, +0.186] | +0.002 [+0.000, +0.005] |
| Random forest | Proposed + inverse-propensity weights | +0.048 [+0.003, +0.088] | +0.055 [-0.074, +0.172] | +0.046 [+0.021, +0.074] | +0.108 [+0.030, +0.229] | +0.007 [+0.000, +0.015] |
| Random forest | KDE-matched background | +0.018 [+0.006, +0.034] | +0.050 [+0.005, +0.105] | +0.010 [-0.001, +0.026] | +0.020 [+0.000, +0.044] | +0.017 [+0.003, +0.035] |
| Random forest | Random background | +0.032 [+0.015, +0.054] | +0.151 [+0.061, +0.233] | +0.001 [-0.003, +0.005] | +0.071 [+0.036, +0.121] | +0.005 [+0.000, +0.012] |
| Random forest | Spatial thinning | +0.151 [+0.100, +0.217] | +0.337 [+0.179, +0.495] | +0.103 [+0.074, +0.137] | +0.272 [+0.171, +0.367] | +0.067 [+0.040, +0.100] |
