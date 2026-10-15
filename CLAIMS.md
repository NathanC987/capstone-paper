# Claims ledger

Every claim the paper makes, where its number comes from and which code
produces it. Numbers in the paper are `\res{key}` macros written by
`examples/paper/build_artifacts.py` (in the code repository) from the study
outputs; nothing is typed by hand. Before submission each author should be
able to explain every row.

Repository paths are relative to the code repository root.

## Method

| Claim | Evidence | Code |
|---|---|---|
| Every decision is a test at alpha = 0.05 with Holm or Bonferroni | `acs-alpha`; config of every output | `src/drift_autopsy/diagnosis.py`, `stats.py`, detectors |
| Label-free stage: Holm over three block tests, gatekeeping for features | diagnosis docstring | `diagnosis.label_free_diagnosis` |
| Prior vs covariate: BBSE reweighting, then weighted feature tests | diagnosis docstring | `diagnosis.bbse_weights`, `_weighted_feature_tests` |
| Audit: accuracy drop test, then LR test of error structure with confidence bins in the null | `const-quantile-bins` | `diagnosis.audit_diagnosis` |
| The diagnosis was frozen before design B ran | design B code and outputs postdate the last change to the default path of `diagnosis.py`; the only later edits add optional arguments (`null`, `precomputed_mmd`) whose defaults reproduce the method, verified by `test_recomputed_verdict_and_precomputed_mmd_match_the_method` and by the exact reproduction of the old 650 windows | git history; `tests/unit/test_baselines_models_and_design_b.py` |
| Old benchmark reproduced exactly (650 windows, 0 differences) | comparison run on `outputs/drift_injection_benchmark_runs.json` (old) vs `outputs/benchmark/acs_income_A_lr_runs.json` | not in the paper text; see the dashboard redesign notes |
| GPU and CPU permutation tests give identical p-values | 14 MMD cases and 6 CLEAR Frechet/PCA cases checked; unit test | `src/drift_autopsy/gpu.py`, `test_gpu_permutation_tests_match_cpu` |

## Benchmark (Tables methods, mechanisms, detectors, estimators; confusion figure)

| Claim | Keys | Source |
|---|---|---|
| Ours names the type in 87 to 94% of design A windows | `bench-a-ours-min/max`, `b-*-a-*-ours-acc` | `outputs/benchmark/summary.json` -> `methods` |
| Rule baselines are significantly worse in every configuration | `bench-nbetter`, `bench-ntests`, arrows in `tab_methods` | `summary.json` -> `paired_tests` (sign-flip over replicates, Holm) |
| Meta-classifier beats ours on design A (leave one state out) | `b-*-a-*-metaclassifier-acc` | `benchmark/metrics.meta_classifier_predictions` |
| Meta-classifier trained on design A falls to 32 to 51% on design B; ours keeps 63 to 82% | `bench-b-meta-min/max`, `bench-b-ours-min/max` | `examples/quickstart/benchmark_summary.py::meta_transfer` |
| Removing the confidence term from the audit null costs about 14 points (Income A, LR) | `b-inc-a-lr-noconfidencenull-diff` | ablation `null="none"` in `audit_diagnosis` |
| The MMD block adds nothing on the benchmark | `b-inc-a-lr-nommd-diff` | ablation `use_mmd=False` in `diagnosis_baselines.ours` |
| Class x confidence null helps on Employment B but is not adopted | `b-emp-b-lr-classconfidencenull-acc` | ablation `null="class_confidence"` |
| Income threshold concept drift is read as no drift; it barely changes accuracy | `b-inc-lr-mech-conceptthreshold-*` | `summary.json` -> `mechanisms` |
| Class-conditional noise is often read as concept drift | `b-*-mech-classnoise-*` | same |
| False alarm rates near alpha (pooled design A controls) | `det-*-none`, `det-*-none-ci` | `tab_detectors` from the design A runs |
| Concept and noise windows share the control inputs, so their detector alarm rates equal the false alarm rate | identical columns in `tab_detectors` | `benchmark/evaluate.run_replicate` (one production sample per replicate) |
| ATC has the smallest estimate error in most columns; CBPE does not win | `est-nbest-atc`, `est-nbest-cbpe` | `tab_estimators`; `estimation.label_free_estimates` |

## Real drift

| Claim | Keys | Source |
|---|---|---|
| No control window is diagnosed as drift (all datasets, both models) | `*-ctrl-type` | study outputs |
| One detector false alarm on a control: domain classifier on CLEAR-10 | `clr-ctrl-dc-p` | `outputs/clear10_drift_results*.json` |
| ACS Income accuracy falls 2015 to 2023 | `inc-ca2015-acc`, `inc-ca2023-acc` | `outputs/folktables_drift_results.json` |
| 2018 occupation recode: share of unseen codes | `inc-ca2018-unseen-occp` | KS localization `unseen_category_share` |
| Occupation SHAP change in 2018 | `inc-ca2018-shap-occp` | SHAP analyzer, Bonferroni bootstrap interval |
| 2019 relationship redesign shows in RELP | `inc-ca2019-eff-relp` | localization effect size (Cramer's V) |
| Race shifts from 2021 after the coding change | `inc-ca2021-eff-rac1p`; Census user note 2021-03 | localization |
| Positive rate rises against the fixed threshold while predictions lag | `inc-ctrl-posrate`, `inc-ca2023-posrate`, `inc-ca2023-predposrate` | study output |
| CA 2015 verdict changed from label noise to no drift with its own audit sample | old vs new output comparison | per-window random streams (`experiments/common.window_rng`) |
| ACS Employment: every window covariate, accuracy changes little | `emp-dacc-maxabs` | `outputs/folktables_employment_drift_results_lr.json` |
| Gas sensor: every batch covariate; BBSE first calls them prior | `gas-*-type`, `gas-*-v-bbsefirst` | `outputs/gas_drift_results_*.json` |
| CLEAR-10: covariate from bucket 4, found by MMD | `clr-windows-covariate` | `outputs/clear10_drift_results.json` |

## Negative findings

| Claim | Keys | Source |
|---|---|---|
| Accuracy estimates are optimistic; on gas batch 8 CBPE estimates about 1 while mean confidence falls, because the low-confidence bins hold only 8 calibration rows (all correct; checked by refitting) | `gas-b8-acc`, `gas-b8-est`, `gas-b8-conf`, `gas-b8-sparse-share`, `gas-b8-sparse-cal-n` | gas output, CBPE metadata `reference_bin_counts` |
| Fused reliability adds nothing beyond confidence on ACS and CLEAR-10; on gas it is unstable (fitted on 4 or 11 errors) | `rel-other-diff-*`, `rel-gas-diff-*`, `rel-gas-*-cal-errors`, `rel-bench-gain-*` | study outputs, benchmark summaries |
| Triage is right where a labelled recent window exists, conservative without one (benchmark recall 6%) | `rem-recent-*`, `rem-norecent-*`, `b-inc-a-lr-triage-recall` | `outputs/remediation_results*.json`, benchmark |
| Concept probe not validated by image tags | `concept-nbuckets-sig`, `concept-b10-rho` | `outputs/clip_concepts/concept_rca_results.json` |

## Facts that need a citation (checked)

- RELP replaced by RELSHIPP from 2019: 2019 PUMS data dictionary (`census2019pums`).
- No standard 2020 one-year release: Census experimental data page (`census2021experimental`).
- New race coding from the 2020 ACS: Census user note 2021-03 (`census2021race`).
- 2018 occupation code revision: `census2020occupation`.
- Gas sensor batches and months: UCI dataset page; Vergara et al. 2012.

## Tasks for the authors

- Read every row above and the generated tables once more against the outputs.
- Choose five suggested reviewers (journal requirement; not chosen here).
- Fill in the funding statement in `main.tex` (acknowledgements are hidden in the anonymous build).
- For review, publish the code at an anonymised address and set it in the
  reproducibility paragraph; switch `\anonymousfalse` for the final version.
