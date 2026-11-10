# Effort-aware pseudo-absences for presence-only pest reports (spotted lanternfly)

Code for a BMC Research Notes *Research note*: does correcting for reporting effort when
generating pseudo-absences improve prediction of **independent, structured survey results**,
when the only training data are **presence-only public reports**?

Data: `lyde.csv` from lydemapr (De Bona et al. 2023, NeoBiota 86:151-168; Zenodo
10.5281/zenodo.12170251, CC BY 4.0). **Use the full `lyde.csv` (about 180 MB), not `lyde_10k.csv`.**

## 1. Quick start (5 minutes)

```bash
python -m pip install -r requirements.txt        # numpy pandas scipy scikit-learn matplotlib pillow
python selftest.py                                # must print SELFTEST PASS (1-2 min, no data needed)

# the real experiment (about 3-6 min on a laptop)
python run_real.py --lyde /path/to/lyde.csv --out results/real

# the virtual-species experiment, truth known (about 10-15 min; resumable)
python run_simulation.py --lyde /path/to/lyde.csv --out results/simulation

# manuscript-ready tables
python make_tables.py --real results/real --sim results/simulation --out results/paper_tables.md
```

Python 3.9+ is fine. Everything is seeded: re-running gives identical numbers on the same library
versions (tiny differences across scikit-learn versions are normal).

## 2. Design

| Step | Choice | Why |
|---|---|---|
| Training data | PUBLIC reports (`individual_reporting`), positives only, bio-years 2019-2021 | the realistic presence-only situation |
| Test data | PROFESSIONAL surveys (`field_survey/management`), bio-years 2022-2023, one label per 10-km cell (any detection) | independent, has true absences, later in time |
| Accessible area M | cells with any record up to 2021 (public or survey; **locations only, never outcomes**) | where observers could have recorded anything; no test-period information |
| Study region | cells within 250 km of a training report | avoids trivially easy far-away absences |
| Test cell filter | at least 3 survey records (sensitivity: 1 and 10) | one empty visit is weak evidence of absence |
| Target | `lyde_present` (sensitivity: `--target established`) | `lyde_established` is missing for about 18% of public reports |

Treatments (all train on presence-only reports; none sees any survey outcome):

1. `random_bg` - random background from M (reference)
2. `thin_bg` - positives thinned to one per 30-km block, random background
3. `kde_bg` - background drawn proportional to the kernel density of training reports (target-group style)
4. `ewc_pa` - **proposed**: 50-km geographic buffer around positives, exclusion of cells inside the presences' environmental envelope, then pseudo-absences sampled proportional to reporting propensity q (percentile of the effort proxy)
5. `ewc_pa_ipw` - `ewc_pa` plus inverse-propensity weights on positives
6. `effort_cov` - effort proxy added as a covariate and held constant at prediction

Models: random forest, and L2-regularised quadratic logistic regression (the MaxEnt-style
presence/background analogue; it is **not** the MaxEnt software - say so in the paper).
Background draws are replicated (default 10) and averaged.

Baselines reported next to every table: `BASE_kde` (smoothed report density) and `BASE_reports`
(log report count). **A model that does not beat `BASE_kde` has not learned anything beyond
"reports are where reports are."**

Evaluation strata (test cells): all; with training reports; with no training reports
(**bias-independent**); core states (>=5% of training reports: PA, NJ); other states (**transfer**).
Metrics: AUC, average precision, continuous Boyce index, and sensitivity / false-positive rate when
the top 10/20/30% of the region is flagged (the threshold uses only the score distribution, never test
labels). CIs: 50-km spatial-block bootstrap of paired differences.

## 3. Important: the two analysis modes

**Mode A - `lyde.csv` only (default).** Features are distance to the invasion origin, longitude and
latitude; the effort proxy is the density of training reports. This is complete and fully tested but is
a *spatial* model: in development it did **not** beat the report-density baseline. Use it as a baseline
and to validate the machinery.

**Mode B - with environmental and effort covariates (recommended for the paper).** Add climate / land /
population rasters so that the models can learn environment, and so that effort is measured
independently of the reports:

```bash
# download yourself (free): WorldClim 2.1 bioclim (10 arc-min) and a 1-km population-density raster (e.g. WorldPop USA)
python -m slf_effort.covariates --lyde /path/to/lyde.csv --out covariates.csv \
    --raster bio1=wc2.1_10m_bio_1.tif --raster bio4=wc2.1_10m_bio_4.tif \
    --raster bio12=wc2.1_10m_bio_12.tif --raster bio6=wc2.1_10m_bio_6.tif \
    --raster logpop=usa_pd_2020_1km.tif:log1p

python run_real.py --lyde /path/to/lyde.csv --covariates covariates.csv \
    --env-cols bio1 bio4 bio6 bio12 --effort-cols logpop --out results/real_cov
```

The extractor prints, per raster, the share of cells with values and min/median/max. **Sanity-check
these** (e.g. WorldClim bio1 over PA/NJ should be roughly 8-14 degrees C; a population density raster
should be non-negative). Cells with missing covariates are dropped and reported. Rasters must be in
geographic lon/lat (EPSG:4326).

## 4. Files

| File | Purpose |
|---|---|
| `selftest.py` | run first; unit tests + both pipelines on synthetic data |
| `run_real.py` | real-data experiment, tables, figures |
| `run_simulation.py` | virtual-species experiment (known truth), resumable |
| `make_tables.py` | Markdown tables for the manuscript |
| `slf_effort/covariates.py` | optional raster -> `covariates.csv` |
| `slf_effort/*.py` | library: data, background treatments, models, metrics, experiment, simulate, plots |
| `tests/test_pipeline.py` | 33 unit tests (including a label-scrambling leakage test) |
| `example_results/` | outputs from my development run (real lyde.csv v3.0.0, full settings, and 4 scenarios x 10 virtual species) plus `paper_tables.md`; your run should reproduce them on the same library versions (`predictions.csv` omitted for size) |

Outputs of `run_real.py`: `table1_data_summary.csv`, `metrics_by_stratum.csv`,
`sensitivity_min_survey_rows.csv`, `paired_vs_random_background.csv`,
`paired_vs_report_density_baseline.csv`, `predictions.csv`, `training_diagnostics.csv`, `run_config.json`,
`fig_map.png`, `fig_delta_auc_vs_random.png`, `fig_delta_fpr_vs_random.png`, `fig_delta_auc_vs_baseline.png`.

## 5. What was and was not verified

Verified by running (Linux, Python 3.13, numpy 2.5, pandas 3.0, scikit-learn 1.9): all 33 unit tests;
`run_real.py` and `run_simulation.py` on the real lyde.csv v3.0.0; the selftest; a GeoTIFF reader test on a
synthetic raster (LZW-compressed float32 with a nodata block).

**Not verified:** reading real WorldClim / WorldPop files (no internet access in the development
environment), and any run with real environmental covariates. The extractor falls back from Pillow to
rasterio if a file cannot be decoded. If both fail, the error message says so; please run the sanity
checks in section 3.

## 6. Known limitations to state in the paper

* Survey locations are not random (they are partly triggered by reports), so metrics measure
  agreement with structured surveys, not accuracy against the true distribution. The zero-report stratum
  and the simulation address this.
* About 97% of public reports are in PA and NJ; results outside them are a transfer test.
* The invasion is not at equilibrium: an unreported suitable cell may be invaded later. The 50-km buffer
  (about two years of the reported maximum annual spread of roughly 25 km) mitigates this.
* Spatial-block bootstrap CIs resample cells, not independent species or regions.
* Simulation parameters are illustrative; conclusions apply to the scenarios simulated.
