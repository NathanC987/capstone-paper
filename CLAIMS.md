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
| Every decision except the PSI alarm (conventional threshold 0.2) is a test at alpha = 0.05 with Holm, weighted Holm or Bonferroni | `acs-alpha`, `acs-psi-threshold`; config of every output | `src/drift_autopsy/diagnosis.py`, `stats.py`, detectors |
| Label-free stage: one weighted Holm family over all feature, prediction and MMD tests | diagnosis docstring | `diagnosis.label_free_diagnosis` |
| Prior vs covariate: BBSE reweighting, then weighted feature tests | diagnosis docstring | `diagnosis.bbse_weights`, `_weighted_feature_tests` |
| Audit: accuracy drop test, then LR test of error structure with confidence bins in the null | `const-quantile-bins` | `diagnosis.audit_diagnosis` |
| The diagnosis was fixed before design B first ran; a later code review found two errors, corrected without regard to results, and every result was regenerated | `fwer-gate-pct`, `fwer-wholm-pct`, `fix-nchanged`, `fix-nwindows` | `examples/quickstart/fwer_check.py` -> `outputs/fwer_check.json`; `outputs/benchmark/prefix_verdicts.json` (pre-correction verdicts) vs the current `*_runs.json`; `diagnosis.label_free_decisions`, `diagnosis._bins` |
| Label-free decisions: weighted Holm over features (sharing 1/3), prediction (1/3) and MMD (1/3); controls FWER over every decision | `fwer-wholm-pct` | `stats.weighted_holm_reject`, `test_weighted_holm_equal_weights_is_holm_and_controls_fwer` |
| Audit fits are exact maximum likelihood (Newton, float64), identical on CPU and GPU | unit test | `stats.logistic_loglik`, `test_logistic_loglik_is_exact_and_device_independent` |
| Before the 2026-10-15 correction, the rewritten benchmark code reproduced the original 650 windows exactly (a check of the refactoring, not a current result; after the correction the verdicts differ by design) | comparison run on `outputs/drift_injection_benchmark_runs.json` (old) | not in the paper text |
| GPU and CPU permutation tests give identical p-values | 14 MMD cases and 6 CLEAR Frechet/PCA cases checked; unit test | `src/drift_autopsy/gpu.py`, `test_gpu_permutation_tests_match_cpu` |

## Benchmark (Tables 3, 4 and 6; Figure 3; estimator results in prose)

| Claim | Keys | Source |
|---|---|---|
| Ours names the type in 86 to 94% of design A windows | `bench-a-ours-min/max`, `b-*-a-*-ours-acc` | `outputs/benchmark/summary.json` -> `methods` |
| Rule baselines are significantly worse in every configuration | `bench-nbetter`, `bench-ntests`, arrows in `tab_methods` | `summary.json` -> `paired_tests` (sign-flip over replicates, Holm) |
| Meta-classifier beats ours on design A (leave one state out) | `b-*-a-*-metaclassifier-acc` | `benchmark/metrics.meta_classifier_predictions` |
| Meta-classifier trained on design A falls to 31 to 51% on design B; ours keeps 62 to 82% | `bench-b-meta-min/max`, `bench-b-ours-min/max` | `examples/quickstart/benchmark_summary.py::meta_transfer` |
| Removing the confidence term from the audit null costs about 15 points (Income A, LR) | `b-inc-a-lr-noconfidencenull-diffabs` | ablation `null="none"` in `audit_diagnosis` |
| The MMD block adds nothing on the benchmark | `b-inc-a-lr-nommd-diff` | ablation `use_mmd=False` in `diagnosis_baselines.ours` |
| Class x confidence null helps on Employment B but is not adopted | `b-emp-b-lr-classconfidencenull-acc` | ablation `null="class_confidence"` |
| Income threshold concept drift is read as no drift; it barely changes accuracy | `b-inc-lr-mech-conceptthreshold-*` | `summary.json` -> `mechanisms` |
| Class-conditional noise is often read as concept drift | `b-*-mech-classnoise-*` | same |
| False alarm rates near alpha (pooled design A controls) | `det-*-none`, `det-*-none-ci` | `tab_detectors` from the design A runs |
| Our diagnosis raised false alarms on 13 of 200 controls (6.5%), within its 2 alpha bound (each stage at alpha) | `diag-fa-*` | `build_artifacts.benchmark` from the design A runs |
| Concept and noise windows share the control inputs, so their detector alarm rates equal the false alarm rate | identical columns in `tab_detectors` | `benchmark/evaluate.run_replicate` (one production sample per replicate) |
| Estimate errors: below `est-bench-none-max` without drift and `est-bench-covariate-max` under covariate shift; whole loss under concept and noise; ATC best in 6 of 8 comparisons, CBPE in 2 | `est-bench-*-min/max`, `est-bench-conceptnoise-cbpe`, `est-nbest-*`, `est-gas-*` | `build_artifacts.estimators` (the table `tab_estimators` is still written but no longer printed); `estimation.label_free_estimates` |
| Every detector false alarm interval contains alpha or lies below it | `det-*-none-ci` | guarded in `build_artifacts.benchmark` (the build fails otherwise) |
| KS, MMD and BBSD catch the same share of prior shifts | `det-bbsd-prior` | guarded in `build_artifacts.benchmark` |

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
| ACS Employment: every window covariate, accuracy changes little | `emp-dacc-maxabs` | `outputs/folktables_employment_drift_results_lr.json` |
| Gas sensor: every batch covariate; BBSE first calls them prior | `gas-*-type`, `gas-*-v-bbsefirst` | `outputs/gas_drift_results_*.json` |
| CLEAR-10: covariate from bucket 4; in buckets 4, 5, 6 and 9 no single dimension shifts and only MMD finds the change | `clr-windownums-covariate`, `clr-windownums-mmdonly` | `outputs/clear10_drift_results.json` (`diagnosis.n_input_shift_dimensions`) |

## Accuracy estimate, reliability and triage (Section 6)

| Claim | Keys | Source |
|---|---|---|
| Accuracy estimates are optimistic; on gas batch 8 CBPE estimates 0.618 against a true 0.330, because drift breaks the confidence-to-accuracy relation (bins with fewer than 5 calibration rows keep the model's own confidence) | `gas-b8-acc`, `gas-b8-est`, `gas-b8-conf` | gas output; `estimation.BinnedAccuracyCalibration` |
| Fused reliability adds nothing beyond confidence on ACS and CLEAR-10; on gas no fusion is learned (4 or 11 calibration errors, fewer than 10 per signal) | `rel-other-diff-*`, `rel-gas-*-cal-errors`, `rel-min-events`, `rel-bench-gain-*` | study outputs; `reliability.fusion.MIN_EVENTS_PER_SIGNAL` |
| Triage is right where a labelled recent window exists, conservative without one (benchmark recall 6%) | `rem-recent-*`, `rem-norecent-*`, `b-inc-a-lr-triage-recall` | `outputs/remediation_results*.json`, benchmark |

## Removed from the paper for length (still in the code and dashboard)

- CAM figure for CLEAR-10 (`gen_cam.pdf` is still generated).
- Concept probe result (`concept-*` keys; no tag agreement in any bucket).
- Remediation table (`tab_remediation`; its key numbers stay in Section 6).
- Estimator table (`tab_estimators`; summarized in prose).

## Novelty and closest work (checked 2026-10-16)

| Claim | Source |
|---|---|
| Roschewitz et al. separate prevalence from covariate shift without labels by prevalence adjustment and retesting (medical images); no concept drift or label noise | MICCAI 2025, LNCS pp. 67-76, doi 10.1007/978-3-032-04981-0_7 (arXiv 2411.07940) |
| DetectShift tests shifts in (X,Y), X, Y, X given Y and Y given X but needs labelled target data (its authors list this as a limitation); no label noise | Information Sciences 649, 119612 (2023) |
| No published method found that separates concept drift from label noise with a small audit, or grades a type diagnosis on held out mechanisms | literature search 2026-10-16 (arXiv, Google Scholar style queries); stated as "to our knowledge" |

## Facts that need a citation (checked)

- RELP replaced by RELSHIPP from 2019: 2019 PUMS data dictionary (`census2019pums`).
- No standard 2020 one-year release: Census experimental data page (`census2021experimental`).
- New race coding from the 2020 ACS: Census user note 2021-03 (`census2021race`).
- 2018 occupation code revision: `census2020occupation`.
- Gas sensor batches and months: UCI dataset page; Vergara et al. 2012.

## Tasks for the authors

- Read every row above and the generated tables once more against the outputs.
- Choose five suggested reviewers (journal requirement; not chosen here).
- Funding statement in the paper: "This research received no external funding" (capstone project; the mentor is the first author).
- Fill in the funding statement in `main.tex` (acknowledgements are hidden in the anonymous build).
- For review, publish the code at an anonymised address and set it in the
  reproducibility paragraph; switch `\anonymousfalse` for the final version.
