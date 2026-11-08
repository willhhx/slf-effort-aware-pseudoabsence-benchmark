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
| analysis | training positive cells | 280777 | 1102 | 100 |
| analysis | accessible-area cells (M) |  | 3269 |  |

## AUC by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.799 | 0.832 | 0.66 | 0.907 | 0.819 |
| - | Baseline: report count | 0.744 | 0.836 | 0.5 | 0.887 | 0.587 |
| MaxEnt-style logistic | Effort covariate held constant | 0.695 | 0.579 | 0.585 | 0.662 | 0.759 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.771 | 0.705 | 0.669 | 0.783 | 0.812 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.77 | 0.704 | 0.668 | 0.78 | 0.81 |
| MaxEnt-style logistic | KDE-matched background | 0.774 | 0.745 | 0.651 | 0.824 | 0.784 |
| MaxEnt-style logistic | Random background | 0.762 | 0.699 | 0.651 | 0.784 | 0.8 |
| MaxEnt-style logistic | Spatial thinning | 0.712 | 0.61 | 0.609 | 0.698 | 0.731 |
| Random forest | Effort covariate held constant | 0.391 | 0.627 | 0.372 | 0.68 | 0.29 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.763 | 0.695 | 0.647 | 0.776 | 0.795 |
| Random forest | Proposed + inverse-propensity weights | 0.761 | 0.69 | 0.644 | 0.773 | 0.792 |
| Random forest | KDE-matched background | 0.683 | 0.769 | 0.342 | 0.864 | 0.452 |
| Random forest | Random background | 0.752 | 0.756 | 0.563 | 0.858 | 0.736 |
| Random forest | Spatial thinning | 0.637 | 0.375 | 0.551 | 0.474 | 0.701 |

## Average precision by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.815 | 0.921 | 0.48 | 0.914 | 0.792 |
| - | Baseline: report count | 0.753 | 0.922 | 0.322 | 0.904 | 0.515 |
| MaxEnt-style logistic | Effort covariate held constant | 0.679 | 0.815 | 0.35 | 0.747 | 0.658 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.761 | 0.862 | 0.44 | 0.824 | 0.779 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.76 | 0.862 | 0.439 | 0.823 | 0.773 |
| MaxEnt-style logistic | KDE-matched background | 0.767 | 0.878 | 0.431 | 0.849 | 0.724 |
| MaxEnt-style logistic | Random background | 0.746 | 0.858 | 0.414 | 0.82 | 0.754 |
| MaxEnt-style logistic | Spatial thinning | 0.69 | 0.817 | 0.375 | 0.757 | 0.59 |
| Random forest | Effort covariate held constant | 0.408 | 0.787 | 0.261 | 0.663 | 0.319 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.728 | 0.831 | 0.44 | 0.759 | 0.775 |
| Random forest | Proposed + inverse-propensity weights | 0.726 | 0.829 | 0.439 | 0.757 | 0.772 |
| Random forest | KDE-matched background | 0.725 | 0.864 | 0.259 | 0.85 | 0.461 |
| Random forest | Random background | 0.765 | 0.875 | 0.35 | 0.861 | 0.701 |
| Random forest | Spatial thinning | 0.558 | 0.655 | 0.344 | 0.526 | 0.584 |

## False-positive rate at 20% alert budget (lower is better) by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.057 | 0.276 | 0.001 | 0.141 | 0.0 |
| - | Baseline: report count | 0.087 | 0.427 | 0.0 | 0.214 | 0.0 |
| MaxEnt-style logistic | Effort covariate held constant | 0.178 | 0.513 | 0.093 | 0.431 | 0.005 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.117 | 0.377 | 0.05 | 0.285 | 0.002 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.118 | 0.382 | 0.05 | 0.287 | 0.002 |
| MaxEnt-style logistic | KDE-matched background | 0.095 | 0.302 | 0.042 | 0.222 | 0.009 |
| MaxEnt-style logistic | Random background | 0.117 | 0.372 | 0.051 | 0.285 | 0.002 |
| MaxEnt-style logistic | Spatial thinning | 0.157 | 0.447 | 0.082 | 0.335 | 0.035 |
| Random forest | Effort covariate held constant | 0.186 | 0.025 | 0.228 | 0.0 | 0.314 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.151 | 0.482 | 0.066 | 0.363 | 0.005 |
| Random forest | Proposed + inverse-propensity weights | 0.158 | 0.503 | 0.069 | 0.378 | 0.007 |
| Random forest | KDE-matched background | 0.072 | 0.337 | 0.004 | 0.166 | 0.007 |
| Random forest | Random background | 0.081 | 0.392 | 0.001 | 0.199 | 0.0 |
| Random forest | Spatial thinning | 0.237 | 0.613 | 0.14 | 0.479 | 0.071 |

## Sensitivity at 20% alert budget by stratum (test cells)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| - | Baseline: report KDE | 0.522 | 0.836 | 0.035 | 0.831 | 0.115 |
| - | Baseline: report count | 0.548 | 0.902 | 0.0 | 0.884 | 0.108 |
| MaxEnt-style logistic | Effort covariate held constant | 0.37 | 0.577 | 0.049 | 0.644 | 0.01 |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | 0.446 | 0.698 | 0.057 | 0.734 | 0.069 |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | 0.445 | 0.696 | 0.057 | 0.732 | 0.069 |
| MaxEnt-style logistic | KDE-matched background | 0.46 | 0.71 | 0.073 | 0.74 | 0.093 |
| MaxEnt-style logistic | Random background | 0.45 | 0.71 | 0.046 | 0.757 | 0.047 |
| MaxEnt-style logistic | Spatial thinning | 0.387 | 0.591 | 0.07 | 0.639 | 0.057 |
| Random forest | Effort covariate held constant | 0.069 | 0.023 | 0.141 | 0.002 | 0.157 |
| Random forest | Effort-weighted constrained PA (proposed) | 0.582 | 0.865 | 0.144 | 0.886 | 0.184 |
| Random forest | Proposed + inverse-propensity weights | 0.6 | 0.883 | 0.163 | 0.91 | 0.194 |
| Random forest | KDE-matched background | 0.512 | 0.834 | 0.014 | 0.83 | 0.096 |
| Random forest | Random background | 0.508 | 0.834 | 0.003 | 0.83 | 0.086 |
| Random forest | Spatial thinning | 0.31 | 0.439 | 0.111 | 0.408 | 0.182 |

## Change in AUC vs random background (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | -0.066 [-0.087, -0.045] | -0.119 [-0.185, -0.079] | -0.066 [-0.091, -0.045] | -0.122 [-0.180, -0.081] | -0.041 [-0.061, -0.022] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | +0.010 [-0.001, +0.020] | +0.007 [-0.011, +0.026] | +0.018 [+0.002, +0.036] | -0.001 [-0.022, +0.013] | +0.012 [-0.002, +0.030] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | +0.008 [-0.001, +0.019] | +0.005 [-0.013, +0.025] | +0.017 [+0.001, +0.034] | -0.004 [-0.025, +0.011] | +0.010 [-0.004, +0.026] |
| MaxEnt-style logistic | KDE-matched background | +0.012 [+0.002, +0.021] | +0.046 [+0.028, +0.072] | +0.000 [-0.012, +0.018] | +0.040 [+0.026, +0.061] | -0.016 [-0.029, -0.001] |
| MaxEnt-style logistic | Spatial thinning | -0.050 [-0.067, -0.030] | -0.089 [-0.126, -0.052] | -0.042 [-0.070, -0.019] | -0.086 [-0.122, -0.059] | -0.068 [-0.101, -0.041] |
| Random forest | Effort covariate held constant | -0.361 [-0.436, -0.272] | -0.129 [-0.222, -0.039] | -0.191 [-0.316, -0.041] | -0.177 [-0.249, -0.109] | -0.445 [-0.561, -0.352] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.011 [-0.016, +0.037] | -0.061 [-0.124, -0.001] | +0.084 [+0.055, +0.120] | -0.082 [-0.135, -0.024] | +0.059 [+0.040, +0.084] |
| Random forest | Proposed + inverse-propensity weights | +0.009 [-0.016, +0.034] | -0.065 [-0.128, -0.003] | +0.081 [+0.053, +0.116] | -0.085 [-0.138, -0.029] | +0.057 [+0.038, +0.082] |
| Random forest | KDE-matched background | -0.069 [-0.100, -0.041] | +0.013 [-0.008, +0.037] | -0.221 [-0.287, -0.155] | +0.006 [-0.007, +0.018] | -0.283 [-0.344, -0.212] |
| Random forest | Spatial thinning | -0.115 [-0.156, -0.080] | -0.380 [-0.490, -0.262] | -0.012 [-0.035, +0.006] | -0.383 [-0.462, -0.310] | -0.034 [-0.056, -0.017] |

## Change in FPR vs random background (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | +0.061 [+0.027, +0.097] | +0.141 [+0.070, +0.217] | +0.041 [+0.015, +0.077] | +0.146 [+0.068, +0.238] | +0.003 [+0.000, +0.013] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | +0.000 [-0.010, +0.010] | +0.005 [-0.031, +0.035] | -0.001 [-0.008, +0.004] | +0.000 [-0.034, +0.025] | +0.000 [+0.000, +0.000] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | +0.001 [-0.009, +0.012] | +0.010 [-0.026, +0.041] | -0.001 [-0.008, +0.004] | +0.003 [-0.033, +0.029] | +0.000 [+0.000, +0.000] |
| MaxEnt-style logistic | KDE-matched background | -0.022 [-0.044, -0.003] | -0.070 [-0.132, -0.018] | -0.009 [-0.028, +0.004] | -0.063 [-0.109, -0.023] | +0.007 [+0.000, +0.016] |
| MaxEnt-style logistic | Spatial thinning | +0.040 [+0.011, +0.067] | +0.075 [+0.000, +0.157] | +0.031 [+0.013, +0.051] | +0.050 [+0.002, +0.104] | +0.033 [+0.013, +0.055] |
| Random forest | Effort covariate held constant | +0.106 [+0.038, +0.170] | -0.367 [-0.497, -0.261] | +0.227 [+0.166, +0.285] | -0.199 [-0.283, -0.110] | +0.314 [+0.235, +0.392] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.070 [+0.021, +0.132] | +0.090 [-0.044, +0.235] | +0.064 [+0.027, +0.109] | +0.164 [+0.035, +0.273] | +0.005 [+0.000, +0.014] |
| Random forest | Proposed + inverse-propensity weights | +0.077 [+0.032, +0.142] | +0.111 [-0.020, +0.250] | +0.068 [+0.031, +0.111] | +0.179 [+0.055, +0.292] | +0.007 [+0.000, +0.016] |
| Random forest | KDE-matched background | -0.009 [-0.022, +0.002] | -0.055 [-0.101, +0.000] | +0.003 [-0.001, +0.008] | -0.033 [-0.057, -0.009] | +0.007 [+0.002, +0.015] |
| Random forest | Spatial thinning | +0.156 [+0.100, +0.223] | +0.221 [+0.020, +0.402] | +0.139 [+0.097, +0.179] | +0.280 [+0.181, +0.403] | +0.071 [+0.036, +0.107] |

## Change in AUC vs report-density (KDE) baseline (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | -0.103 [-0.143, -0.068] | -0.252 [-0.341, -0.179] | -0.075 [-0.115, -0.034] | -0.246 [-0.360, -0.163] | -0.060 [-0.098, -0.023] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | -0.028 [-0.058, -0.003] | -0.127 [-0.192, -0.076] | +0.009 [-0.031, +0.053] | -0.125 [-0.204, -0.071] | -0.007 [-0.032, +0.024] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | -0.029 [-0.059, -0.004] | -0.128 [-0.194, -0.077] | +0.007 [-0.033, +0.051] | -0.127 [-0.207, -0.072] | -0.009 [-0.035, +0.022] |
| MaxEnt-style logistic | KDE-matched background | -0.025 [-0.051, +0.001] | -0.087 [-0.131, -0.043] | -0.009 [-0.047, +0.039] | -0.083 [-0.157, -0.041] | -0.035 [-0.076, -0.000] |
| MaxEnt-style logistic | Random background | -0.037 [-0.068, -0.009] | -0.133 [-0.189, -0.080] | -0.009 [-0.047, +0.032] | -0.124 [-0.204, -0.070] | -0.019 [-0.052, +0.012] |
| MaxEnt-style logistic | Spatial thinning | -0.087 [-0.131, -0.053] | -0.222 [-0.304, -0.160] | -0.051 [-0.103, -0.006] | -0.210 [-0.296, -0.133] | -0.088 [-0.133, -0.043] |
| Random forest | Effort covariate held constant | -0.408 [-0.478, -0.337] | -0.205 [-0.294, -0.121] | -0.288 [-0.403, -0.157] | -0.227 [-0.296, -0.159] | -0.529 [-0.632, -0.436] |
| Random forest | Effort-weighted constrained PA (proposed) | -0.036 [-0.065, -0.011] | -0.137 [-0.203, -0.085] | -0.013 [-0.046, +0.020] | -0.132 [-0.196, -0.077] | -0.025 [-0.047, +0.001] |
| Random forest | Proposed + inverse-propensity weights | -0.038 [-0.068, -0.012] | -0.141 [-0.203, -0.087] | -0.016 [-0.047, +0.017] | -0.135 [-0.196, -0.086] | -0.027 [-0.050, +0.001] |
| Random forest | KDE-matched background | -0.116 [-0.156, -0.082] | -0.063 [-0.092, -0.032] | -0.318 [-0.389, -0.230] | -0.044 [-0.063, -0.026] | -0.367 [-0.444, -0.295] |
| Random forest | Random background | -0.047 [-0.061, -0.034] | -0.076 [-0.105, -0.047] | -0.097 [-0.125, -0.067] | -0.050 [-0.071, -0.031] | -0.084 [-0.111, -0.055] |
| Random forest | Spatial thinning | -0.162 [-0.208, -0.111] | -0.456 [-0.562, -0.344] | -0.109 [-0.145, -0.075] | -0.433 [-0.500, -0.361] | -0.118 [-0.152, -0.087] |

## Change in FPR vs report-density (KDE) baseline (95% spatial-block bootstrap CI)
| model | treatment | All test cells | Cells with reports | Cells with no reports | Core states (PA/NJ) | Other states (transfer) |
|---|---|---|---|---|---|---|
| MaxEnt-style logistic | Effort covariate held constant | +0.121 [+0.063, +0.187] | +0.236 [+0.121, +0.361] | +0.091 [+0.048, +0.132] | +0.290 [+0.156, +0.441] | +0.005 [+0.000, +0.013] |
| MaxEnt-style logistic | Effort-weighted constrained PA (proposed) | +0.059 [+0.017, +0.111] | +0.101 [+0.004, +0.203] | +0.049 [+0.020, +0.080] | +0.144 [+0.057, +0.259] | +0.002 [+0.000, +0.005] |
| MaxEnt-style logistic | Proposed + inverse-propensity weights | +0.060 [+0.017, +0.112] | +0.106 [+0.010, +0.205] | +0.049 [+0.020, +0.080] | +0.146 [+0.058, +0.260] | +0.002 [+0.000, +0.005] |
| MaxEnt-style logistic | KDE-matched background | +0.038 [-0.001, +0.073] | +0.025 [-0.074, +0.148] | +0.041 [+0.018, +0.069] | +0.081 [+0.019, +0.180] | +0.009 [+0.002, +0.020] |
| MaxEnt-style logistic | Random background | +0.059 [+0.016, +0.110] | +0.095 [+0.012, +0.198] | +0.050 [+0.022, +0.083] | +0.144 [+0.062, +0.264] | +0.002 [+0.000, +0.005] |
| MaxEnt-style logistic | Spatial thinning | +0.099 [+0.042, +0.159] | +0.171 [+0.057, +0.301] | +0.081 [+0.049, +0.120] | +0.194 [+0.093, +0.324] | +0.035 [+0.014, +0.055] |
| Random forest | Effort covariate held constant | +0.129 [+0.065, +0.200] | -0.251 [-0.365, -0.138] | +0.227 [+0.168, +0.284] | -0.141 [-0.222, -0.076] | +0.314 [+0.242, +0.385] |
| Random forest | Effort-weighted constrained PA (proposed) | +0.093 [+0.038, +0.158] | +0.206 [+0.106, +0.330] | +0.064 [+0.034, +0.103] | +0.222 [+0.112, +0.346] | +0.005 [+0.000, +0.013] |
| Random forest | Proposed + inverse-propensity weights | +0.100 [+0.047, +0.165] | +0.226 [+0.118, +0.353] | +0.068 [+0.034, +0.103] | +0.237 [+0.130, +0.367] | +0.007 [+0.000, +0.015] |
| Random forest | KDE-matched background | +0.014 [+0.005, +0.024] | +0.060 [+0.029, +0.100] | +0.003 [-0.002, +0.008] | +0.025 [+0.008, +0.050] | +0.007 [+0.002, +0.016] |
| Random forest | Random background | +0.024 [+0.011, +0.039] | +0.116 [+0.058, +0.174] | +0.000 [-0.004, +0.003] | +0.058 [+0.029, +0.101] | +0.000 [+0.000, +0.000] |
| Random forest | Spatial thinning | +0.179 [+0.112, +0.240] | +0.337 [+0.152, +0.506] | +0.139 [+0.102, +0.186] | +0.338 [+0.237, +0.449] | +0.071 [+0.042, +0.101] |

## Virtual species: change in AUC vs random background, Unreported cells vs truth (mean ± 1.96 SE over 10 species; win rate)
| scenario | model | Spatial thinning | KDE-matched background | Effort-weighted constrained PA (proposed) | Proposed + inverse-propensity weights | Effort covariate held constant |
|---|---|---|---|---|---|---|
| adverse | MaxEnt-style logistic | -0.000 ± 0.002 (wins 50%) | -0.013 ± 0.007 (wins 10%) | +0.001 ± 0.007 (wins 50%) | +0.002 ± 0.008 (wins 50%) | +0.005 ± 0.005 (wins 80%) |
| adverse | Random forest | -0.013 ± 0.005 (wins 10%) | -0.042 ± 0.008 (wins 0%) | +0.016 ± 0.009 (wins 90%) | +0.014 ± 0.011 (wins 90%) | +0.013 ± 0.008 (wins 90%) |
| confounded | MaxEnt-style logistic | -0.000 ± 0.003 (wins 40%) | -0.004 ± 0.002 (wins 20%) | -0.007 ± 0.005 (wins 10%) | -0.007 ± 0.005 (wins 10%) | +0.001 ± 0.003 (wins 50%) |
| confounded | Random forest | -0.017 ± 0.003 (wins 0%) | -0.026 ± 0.007 (wins 0%) | +0.002 ± 0.007 (wins 50%) | -0.003 ± 0.009 (wins 40%) | +0.002 ± 0.005 (wins 60%) |
| confounded_strong | MaxEnt-style logistic | +0.004 ± 0.005 (wins 70%) | +0.002 ± 0.004 (wins 40%) | -0.001 ± 0.005 (wins 60%) | -0.001 ± 0.008 (wins 60%) | +0.004 ± 0.009 (wins 80%) |
| confounded_strong | Random forest | -0.008 ± 0.006 (wins 20%) | -0.012 ± 0.006 (wins 10%) | +0.004 ± 0.006 (wins 70%) | +0.004 ± 0.007 (wins 80%) | -0.019 ± 0.014 (wins 20%) |
| independent | MaxEnt-style logistic | -0.002 ± 0.003 (wins 50%) | -0.005 ± 0.004 (wins 20%) | -0.003 ± 0.005 (wins 20%) | -0.003 ± 0.005 (wins 40%) | +0.002 ± 0.004 (wins 60%) |
| independent | Random forest | -0.019 ± 0.005 (wins 0%) | -0.020 ± 0.004 (wins 0%) | +0.006 ± 0.008 (wins 60%) | +0.006 ± 0.007 (wins 60%) | +0.003 ± 0.008 (wins 70%) |

## Virtual species: change in AUC vs random background, Biased survey sample (mean ± 1.96 SE over 10 species; win rate)
| scenario | model | Spatial thinning | KDE-matched background | Effort-weighted constrained PA (proposed) | Proposed + inverse-propensity weights | Effort covariate held constant |
|---|---|---|---|---|---|---|
| adverse | MaxEnt-style logistic | -0.000 ± 0.003 (wins 50%) | -0.013 ± 0.008 (wins 10%) | +0.001 ± 0.005 (wins 50%) | +0.000 ± 0.004 (wins 40%) | +0.004 ± 0.002 (wins 90%) |
| adverse | Random forest | -0.010 ± 0.004 (wins 10%) | -0.044 ± 0.010 (wins 0%) | +0.014 ± 0.009 (wins 90%) | +0.012 ± 0.009 (wins 70%) | +0.009 ± 0.005 (wins 90%) |
| confounded | MaxEnt-style logistic | -0.003 ± 0.003 (wins 20%) | -0.006 ± 0.003 (wins 10%) | -0.006 ± 0.003 (wins 10%) | -0.008 ± 0.002 (wins 0%) | -0.000 ± 0.001 (wins 40%) |
| confounded | Random forest | -0.019 ± 0.005 (wins 0%) | -0.028 ± 0.007 (wins 0%) | +0.001 ± 0.009 (wins 60%) | -0.003 ± 0.009 (wins 40%) | -0.000 ± 0.003 (wins 50%) |
| confounded_strong | MaxEnt-style logistic | +0.003 ± 0.005 (wins 50%) | -0.000 ± 0.006 (wins 30%) | -0.001 ± 0.005 (wins 40%) | -0.002 ± 0.008 (wins 50%) | -0.002 ± 0.007 (wins 40%) |
| confounded_strong | Random forest | -0.007 ± 0.006 (wins 10%) | -0.013 ± 0.010 (wins 10%) | -0.001 ± 0.007 (wins 50%) | -0.003 ± 0.008 (wins 40%) | -0.017 ± 0.010 (wins 20%) |
| independent | MaxEnt-style logistic | -0.002 ± 0.003 (wins 40%) | -0.005 ± 0.004 (wins 20%) | -0.004 ± 0.003 (wins 30%) | -0.004 ± 0.003 (wins 20%) | +0.001 ± 0.002 (wins 70%) |
| independent | Random forest | -0.022 ± 0.005 (wins 0%) | -0.024 ± 0.008 (wins 0%) | +0.004 ± 0.004 (wins 60%) | +0.003 ± 0.004 (wins 60%) | +0.002 ± 0.007 (wins 50%) |
