# Testing of the Proposed System {#ch:testing}

A monitoring system makes claims about error rates, so testing it means more than checking that the code runs. This chapter states what the testing had to establish, describes the kinds of test used, lists the test cases with their results and draws conclusions from them.

## Introduction to Testing {#sec:test-intro}

The testing had three objectives. The first was functional: every module must do what its requirement in Section @sec:fr says. The second was statistical: every test must hold its stated error rate and the diagnosis must name the drift type correctly when the truth is known. The third concerned the system as a whole: the full pipeline must behave sensibly on real data and the dashboard must present every study without failing.

The scope covers the Python package, the study scripts, the benchmark and the dashboard. All tests ran on the workstation of Section @sec:tools under Python 3.14 with pytest 9.0. The strategy was layered: unit tests for each routine, simulations of error rates for the statistical procedures, the injection benchmark for the diagnosis, real-data studies with control windows for the whole system and integration tests for the dashboard. The automated suite was run again on 30 October 2026 for this report; its output is kept in the project folder.

## Types of Tests Considered {#sec:test-types}

Each kind of test below was chosen because it checks a different claim the system makes.

- **Unit tests** (\res{bb-tests-unit} tests) check single routines against known answers: the Holm procedure against its step-down definition, the weighted KS test against SciPy with unit weights, the chi-square pooling rule, the BBSE weights on a known prior shift, the CBPE estimate on a labeled reference and each drift injector against the definition of its type.
- **Smoke tests** (\res{bb-tests-smoke} tests) check that the main objects can be created and that the basic pipeline runs end to end on small data.
- **Integration tests** (\res{bb-tests-integration} tests) load every study report into the dashboard, build every chart and plain-language note, check that the decision path shown matches the verdicts and render the whole application without exceptions.
- **Statistical validation** checks error rates by simulation: the MMD permutation test and the weighted Holm procedure must not reject a true null more often than α and the family-wise error of the label-free decisions was simulated with \res{bb-fwer-reps} replicates.
- **Model validation** grades the diagnosis on the injection benchmark, where the true type is known, against rule baselines, a learned meta-classifier and ablations of the procedure (Section @sec:graphs).
- **System tests on real data** run the whole pipeline on the four real datasets, where the control windows must stay quiet and the verdicts must agree with the documented causes.
- **Performance tests** record the time each stage takes on every window.
- **Reproducibility tests** check that seeded components (permutation tests, SHAP, gradient boosting, strategies) give identical results when run twice and that the GPU and CPU versions of the permutation tests agree.

Security and load tests were not considered relevant: the system runs locally on public data, serves no external users and processes batches rather than requests.

## Test Case Scenarios {#sec:test-cases}

Table @tab:testcases lists the main test case scenarios. Each is tied to a requirement of Chapter @ch:req and the last column gives the outcome with the test or result that supports it.

Table: Test case scenarios and their results {#tab:testcases widths=0.8,1.3,2.2,2.1,2.1,1.4 size=8.5}
| ID | Requirement | Input / precondition | Expected result | Actual result | Status / evidence |
|---|---|---|---|---|---|
| TC-01 | FR-01 | Dataset with a target of the wrong length; invalid detector options | Rejected with a clear error | Rejected | Pass; test_dataset_and_detector_options_are_validated |
| TC-02 | FR-01 | Nominal and numeric features in one window | KS skips nominal features; localizer uses chi-square for them | As expected | Pass; test_ks_skips_categorical_and_localizer_uses_chi2 |
| TC-03 | FR-04 | Two samples from the same distribution, many repetitions | MMD rejects in at most about α of runs | Within α | Pass; test_mmd_permutation_test_controls_type_one_error |
| TC-04 | FR-04 | One large-scale feature hiding a shift in a small one | Standardized MMD still detects the shift | Detected | Pass; test_mmd_standardize_exposes_shift_hidden_by_large_scale_feature |
| TC-05 | FR-04 | Production values outside the reference range | PSI counts them instead of dropping them | Counted | Pass; test_psi_counts_values_outside_reference_range |
| TC-06 | FR-05 | Labeled reference with known accuracy | CBPE estimate close to the true accuracy | Close | Pass; test_cbpe_estimates_accuracy_from_labelled_reference |
| TC-07 | FR-06 | Planted shift in one feature | Only that feature is flagged after Holm correction | Only that feature | Pass; test_univariate_localizer |
| TC-08 | FR-07, NFR-03 | Several true nulls and one shifted feature | Weighted Holm with equal weights equals Holm; family-wise error at most α | Equal; error at most α | Pass; test_weighted_holm_equal_weights_is_holm_and_controls_fwer; simulation \res{fwer-wholm-pct}% |
| TC-09 | FR-07 | Pure prior shift injected | BBSE recovers the new prior; verdict prior shift | Recovered; prior | Pass; test_bbse_recovers_a_prior_shift |
| TC-10 | FR-07, FR-08 | One window of each injected type and one control | Each type named correctly | All five named | Pass; test_diagnosis_names_each_injected_type |
| TC-11 | FR-08 | Audit with nominal categories, some absent from the audit | Bins counted on the audit rows only | As expected | Pass; test_audit_bins_count_categories_in_the_audit_only |
| TC-12 | FR-09 | Model with real change and pure noise | SHAP intervals flag the real change only | As expected | Pass; test_shap_change_intervals_separate_noise_from_real_change |
| TC-13 | FR-10 | Calibration part with too few wrong predictions | Fusion falls back to confidence risk | Falls back | Pass; test_fusion_falls_back_without_enough_errors |
| TC-14 | FR-11 | Correctable covariate shift; concept shift | Triage escalates on the first and holds on the second | As expected | Pass; test_triage_escalates_on_correctable_covariate_shift_and_iw_recovers, test_triage_holds_on_concept_shift |
| TC-15 | FR-12, FR-13 | Every study report | Dashboard loads all reports, draws every chart and renders without exceptions | As expected | Pass; \res{bb-tests-integration} integration tests |
| TC-16 | FR-14 | Each injector applied to real rows | Each injector changes only what its type allows | As expected | Pass; five injector tests |
| TC-17 | NFR-01 | \res{det-ncontrols} benchmark control windows | Each detector's false alarm CI contains α or lies below it | As expected | Pass; Section @sec:graphs |
| TC-18 | NFR-02 | Benchmark control windows through the full diagnosis | Drift verdicts in at most 2α = \res{diag-fa-bound-pct}% | \res{diag-fa-pct}% | Pass; Section @sec:graphs |
| TC-19 | System | Real control windows of all four datasets | No drift verdict on any control window | None | Pass; Section @sec:real |
| TC-20 | NFR-04 | Every real window | Analysis within a daily monitoring cycle | At most \res{bb-time-max} s | Pass; Section @sec:cost |
| TC-21 | NFR-06 | Seeded components run twice; GPU against CPU | Identical results | Identical | Pass; test_strategies_are_deterministic, test_gpu_permutation_tests_match_cpu |
| TC-22 | NFR-07 | Full automated suite | All tests pass | \res{bb-tests-total} passed in \res{bb-tests-seconds} s | Pass; pytest run of 30 October 2026 |

## Inference Drawn from the Test Cases {#sec:test-inference}

All \res{bb-tests-total} automated tests pass and every test case in Table @tab:testcases met its expected result. The statistical tests matter most, because they back the error rates the system promises. The family-wise error of the label-free decisions came out at \res{fwer-wholm-pct}% against a target of \res{fwer-alpha-pct}%. The rule used before the correction, which tested the blocks first and then the features at the level the block was rejected at, came out at \res{fwer-gate-pct}%: it spent α twice. On the benchmark control windows the full diagnosis raised a false verdict on \res{diag-fa-pct}% of windows, below its bound of \res{diag-fa-bound-pct}%.

Testing also found defects. The simulation above exposed the error in the label-free stage and a code review found that the audit counted the categories of nominal features on all rows instead of the audit rows only. Both were fixed, a regression test was added for each (TC-08 and TC-11) and every result was produced again, which changed the verdict in \res{fix-nchanged} of the \res{fix-nwindows} benchmark windows. Earlier fixes are guarded in the same way: tests now check that SHAP explains the positive-class probability of the full model pipeline, that the MMD test standardizes its inputs, that CBPE stays finite when a confidence bin of the reference is empty and that permutation p values are seeded.

Two limits remain. The automated suite checks behavior on small and synthetic data and does not replace the benchmark and real-data studies, which take hours rather than seconds. And usability was checked by the team and the mentor reviews, not by a study with outside users, so the usability requirement is met only in the sense of NFR-08.
