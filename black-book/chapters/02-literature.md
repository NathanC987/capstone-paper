# Literature Survey {#ch:lit}

This chapter reports the literature survey, a search of granted and published patents, the conclusions we drew, a comparison with the closest existing systems and the feasibility analysis.

## Brief Overview of the Literature Survey {#sec:lit-overview}

The survey asked which parts of drift monitoring are solved and which are not. We searched IEEE Xplore, the ACM Digital Library, SpringerLink, arXiv and Google Scholar for dataset shift, label shift, concept drift, label noise, drift detection and performance estimation without labels. Two surveys of concept drift [@gama2014survey; @lu2019learning], a formal characterization of the kinds of drift [@webb2016characterizing] and a book on dataset shift [@quionero2009dataset] served as starting points and we followed their references forward and backward.

A paper was kept if it proposed or evaluated a method for detecting, estimating or explaining a shift, or supplied data with a documented shift.

## Related Works / Research Papers Referred {#sec:related}

Table @tab:papers lists the method, findings and limitations of each paper that shaped the design, with the inference we drew for this project.

Table: Research papers referred, with the inference drawn for this project {#tab:papers widths=1.7,2.3,2.6,3.0 size=9}
| Paper | Method / approach | Key findings | Limitations / inference |
|---|---|---|---|
| Moreno-Torres et al., 2012 [@moreno2012unifying] | Taxonomy of dataset shift by the part of the joint distribution that changes | Defines covariate shift, prior shift and concept shift precisely | Gives definitions, not tests; we test each definition directly |
| Gama et al., 2004 [@gama2004ddm] | Drift detection method: tracks the error rate of the model online | Detects concept drift as a rise in errors | Needs a label for every prediction and cannot tell concept drift from label noise |
| Bifet and Gavaldà, 2007 [@bifet2007learning] | ADWIN: adaptive windows over a data stream | Detects change in a stream with bounds on false alarms | Watches one statistic; says that a change happened, not its type |
| Gretton et al., 2012 [@gretton2012kernel] | Kernel two-sample test (maximum mean discrepancy) | Detects differences between multivariate distributions | Sees joint changes that per-feature tests miss; used as one block of our label-free stage |
| Lopez-Paz and Oquab, 2017 [@lopezpaz2017c2st] | Classifier two-sample test | A classifier that separates two samples better than chance shows that they differ | Used as a baseline detector; gives no drift type |
| Rabanser et al., 2019 [@rabanser2019failing] | Compares univariate, kernel, classifier and black-box shift detectors on injected shift | Black-box shift detection on the model outputs works best overall | Detects shift but does not name its type; their injected benchmark inspired ours |
| Lipton et al., 2018 [@lipton2018bbse] | Black-box shift estimation of the new class prior from the confusion matrix | Recovers label shift from any classifier | Assumes the inputs within each class do not change; we test that assumption |
| Maia Polo et al., 2023 [@maiapolo2023detectshift] | DetectShift: tests each part of the joint distribution | Names shift types with error control | Needs labeled production data; does not treat label noise |
| Roschewitz et al., 2025 [@roschewitz2025shiftid] | Resamples reference data to the estimated prevalence and re-tests the features | Separates prevalence shift from covariate shift on medical images without labels | Our label-free stage follows the same idea with weights and one error-controlled family |
| Hendrycks and Gimpel, 2017 [@hendrycks2017baseline] | Maximum softmax probability as a baseline signal | Confidence separates correct from wrong predictions and in- from out-of-distribution inputs | Basis of average confidence, an accuracy estimate we compare |
| Guillory et al., 2021 [@guillory2021predicting] | Difference of confidences between reference and target | Predicts accuracy change under shift | Assumes confidence stays calibrated; compared as an estimator |
| Garg et al., 2022 [@garg2022atc] | Average thresholded confidence | Accurate accuracy estimates on many shifts | Fails when the confidence-accuracy link breaks; compared as an estimator |
| Kivimäki et al., 2026 [@kivimaki2025performance] | Confidence-based performance estimation with calibrated confidence | Estimates the confusion matrix and accuracy without labels | Our main accuracy estimate, read as an upper bound when confidence misleads |
| Ovadia et al., 2019 [@ovadia2019trust] | Evaluates predictive uncertainty under dataset shift | Models stay confident while accuracy falls | Explains why label-free estimates can be optimistic |
| Lundberg and Lee, 2017 [@lundberg2017unified] | Shapley additive explanations | Attributes each prediction to its input features | Used to compare what the model relies on before and after a shift |
| Ding et al., 2021 [@ding2021retiring] | Folktables: prediction tasks from the American Community Survey | Real distribution shift across years and states | Our main source of real tabular drift |
| Lin et al., 2021 [@lin2021clear] | CLEAR: a time-ordered image benchmark from Flickr | Natural drift of image content over a decade | Our source of real image drift |

The definitions of Moreno-Torres et al. gave the project its vocabulary and DetectShift its main requirement: a type diagnosis that works from unlabeled data plus a small audit instead of labeled production data. Every detector in the table reports that a shift happened, not its type, so the detectors serve as building blocks. The accuracy estimates all read the model's confidence, which can stay high while accuracy falls [@ovadia2019trust], so they can be too optimistic exactly when they matter most.

## Patent Search {#sec:patents}

We searched Google Patents and Espacenet on 30 October 2026 for "data drift" and "concept drift" combined with "machine learning model", "monitoring", "label shift" and "root cause" and read the claims of the most relevant results. Table @tab:patents lists the six patents closest to this project, with their status as shown by Google Patents.

Table: Patents closest to the project, as checked on 30 October 2026 {#tab:patents widths=1.7,2.4,1.6,1.4,3.2 size=9}
| Number and office | Title | Assignee | Status and date | What it claims and how it differs |
|---|---|---|---|---|
| US 10 762 444 B2 [@fly2020realtime] | Real-time drift detection in machine learning systems and applications | Quickpath, Inc. | Granted, 1 Sep. 2020; active | Compares live score distributions with training scores and alerts on significant drift; does not name a drift type |
| US 11 568 167 B2 [@hines2023drift] | Detecting drift between data used to train and data used to execute a machine learning model | Arthur AI, Inc. | Granted, 31 Jan. 2023; active | Scores each production row against a density model of the training data and triggers retraining past a threshold; no type diagnosis or error control |
| US 12 199 847 B2 [@kolar2025anomaly] | Anomaly detection of model performance in an MLOps platform | Cisco Technology, Inc. | Granted, 14 Jan. 2025; active | Correlates drops in measured accuracy with feature shifts and tags the most correlated feature as the probable cause; needs accuracy measurements |
| US 12 282 384 B2 [@gosala2025drift] | Systems and methods for detecting drift | Jio Platforms Limited | Granted, 22 Apr. 2025; active | Compares model predictions with reference values and flags drift when the error passes a threshold; does not separate drift types |
| EP 4 459 516 A1 [@kroger2024drift] | Drift detection for machine learning operations | Siemens AG | Application published 6 Nov. 2024; withdrawn | Compares normal and outlier subsets of old and new measurements to predict drift and choose retraining or remodeling |
| EP 4 577 950 A1 [@zhang2025realtime] | Real time detection, prediction and remediation of machine learning model drift in asset hierarchy | Hitachi Vantara LLC | Application published 2 Jul. 2025; pending | Detects data and concept drift in sensor time series with the population stability index and clustering, forecasts drift and remediates |

The patents show that drift detection and alerting are well protected and two of them go as far as suggesting a likely cause. None of them names the four drift types of this project, none separates concept drift from label noise and none controls the error rate across its decisions. The audit test and the error-controlled diagnosis of ResilientAI therefore do not appear to fall within the claims we read. This is a technical reading for the purpose of this report, not a legal opinion on freedom to operate.

## Inference Drawn {#sec:inference}

Three conclusions came out of the survey and shaped the design of ResilientAI.

First, detection is a solved part of the problem and diagnosis is not. Good label-free tests exist and the system should reuse them rather than invent new detectors. The new work should go into naming the type of a detected shift.

Second, the gap that matters most is between concept drift and label noise. Both leave the inputs untouched, so no label-free test can see them and both raise the error rate, so an error-rate monitor confuses them. Some labels are therefore unavoidable. The question the project had to answer was how few labels would do and how to use them so that the two types come apart. The answer we developed, described in Chapter @ch:impl, is to ask whether the change in errors depends on an input feature beyond what the model's own confidence explains.

Third, a diagnosis must be judged fairly, since a method tuned on its own benchmark looks good by construction. This led to a benchmark with drift mechanisms held out from the design and to a stated error rate for every decision.

## Comparison with Existing Systems {#sec:comparison}

Table @tab:compare compares ResilientAI with the existing systems closest to it.

Table: Comparison of ResilientAI with existing systems {#tab:compare widths=1.6,2.2,2.0,2.0,2.4 size=9}
| System / paper | Features / method | Strengths | Limitations | Difference in proposed work |
|---|---|---|---|---|
| Error-rate monitors (DDM, ADWIN) [@gama2004ddm; @bifet2007learning] | Track the error rate online | Simple; detect concept drift | Need all labels; cannot separate concept drift from label noise | Labels only for a small audit; separates the two |
| Black-box shift detection [@rabanser2019failing] | Two-sample tests on model outputs | Strong, label-free detection | No drift type, no accuracy estimate | Detection is one stage of a full diagnosis |
| Black-box shift estimation [@lipton2018bbse] | Estimates the new class prior | Label-free; works with any classifier | Assumes pure label shift | Tests the assumption before naming prior shift |
| CBPE and monitoring libraries [@kivimaki2025performance; @klaise2020monitoring] | Accuracy estimates, detectors, dashboards | Practical, packaged tools | No type diagnosis; estimates trust confidence | Adds diagnosis; reads the estimate as an upper bound |
| DetectShift [@maiapolo2023detectshift] | Tests each part of the joint distribution | Error-controlled type tests | Needs labeled production data; no label noise | Unlabeled data plus a few hundred late labels; adds label noise |
| Roschewitz et al. [@roschewitz2025shiftid] | Prevalence-adjusted re-testing of features | Separates prior from covariate shift without labels | Two types only | Same idea inside a four-type, error-controlled procedure |
| Drift patents [@fly2020realtime; @kolar2025anomaly; @gosala2025drift] | Distribution comparison, thresholds, correlation with accuracy | Deployed in industry | Thresholds without error control; no type diagnosis | Hypothesis tests with a stated error rate; four types |

Roschewitz et al. come closest, separating prior from covariate shift without labels, while DetectShift names types only when the production data are labeled. ResilientAI is the only one of these systems that separates concept drift from label noise and is tested on held-out drift.

## Feasibility Analysis {#sec:feasibility}

Before committing to the project we checked whether it could be built with the resources of a student team and whether it raised any legal or ethical concern.

### Technical Feasibility

Every building block is a well-understood test or model with a mature open-source implementation, such as scikit-learn [@pedregosa2011scikit] and SciPy [@virtanen2020scipy]; the data are public. The heaviest computation, the injection benchmark, took \res{bench-total-hours} hours on a desktop processor with \res{const-cpu-cores} cores and no production window took longer than \res{bb-time-max} seconds to analyze (Section @sec:cost). The project was therefore technically feasible on the team's own hardware.

### Economic and Financial Feasibility

The project needed no purchase. Table @tab:budget gives the budget, with the electricity cost estimated from the measured running time and the processor's rated maximum power.

Table: Proposed and actual budget of the project {#tab:budget widths=2.6,3.4,1.4 size=10}
| Item | Basis | Cost (₹) |
|---|---|---|
| Development workstation (Intel Core i5-14600K, 32 GB memory, NVIDIA RTX 4070) | Already owned by a team member; no purchase | 0 |
| Software: Python, scikit-learn, SciPy, PyTorch, SHAP, Streamlit, LibreOffice | Open-source licences | 0 |
| Datasets: Folktables ACS, UCI gas sensor array, CLEAR-10 | Free for research use | 0 |
| Cloud computing and paid services | Not used | 0 |
| Electricity for the experiments | \res{bb-energy-total-kwh} kWh at an assumed ₹10 per kWh | \res{bb-energy-total-inr} |
| Total | | \res{bb-energy-total-inr} |

### Cost-effectiveness Analysis

The alternative to a monitor like ResilientAI is to label production data regularly. Labeling every window of several thousand rows costs far more than an audit of \res{acs-audit-n} rows and the monitor itself runs on ordinary hardware in seconds to minutes per window, so its running cost is small next to that of labeling or of a model failure that goes unnoticed.

### Operational Feasibility and Risk Analysis

The system runs as Python scripts and a dashboard, so it fits into an existing batch workflow without new infrastructure. Table @tab:risk lists the main risks we identified and how each was mitigated.

Table: Risks and their mitigation {#tab:risk widths=2.4,1,3.6 size=9.5}
| Risk | Likelihood | Mitigation |
|---|---|---|
| False alarms from testing many features and detectors | High | Weighted Holm procedure keeps the family-wise error rate at α; checked by simulation and on control windows |
| A diagnosis tuned to its own benchmark | Medium | Held-out design B; diagnosis frozen before design B was first run |
| Errors in the statistical code | Medium | \res{bb-tests-total} automated tests; code review; two errors found and every result regenerated |
| Label-free accuracy estimate misleads under shift | Medium | Reported as an upper bound; four estimators compared |
| Long runs overload the machine | Medium | Capped worker counts and one heavy job at a time |
| Data access or format changes (2020 ACS release, renamed variables) | Low | Cached data; documented mappings (RELSHIPP to RELP) |

### Environmental and Sustainability Feasibility

The project uses no special hardware and no cloud resources. The experiments consumed about \res{bb-energy-total-kwh} kWh of electricity in total, an upper-bound estimate explained in Section @sec:sustain, which corresponds to about \res{bb-co2-total-kg} kg of carbon dioxide at the average emission factor of the Indian grid. Design choices that keep computation low are described in Section @sec:sustain-design.

### Legal, Ethical and Privacy Feasibility

All datasets are public and licensed for research. The American Community Survey microdata are released by the United States Census Bureau under its terms of use and contain no names or addresses; the Folktables code that downloads them is under the MIT licence. The UCI gas sensor dataset and the CLEAR benchmark are released under the Creative Commons Attribution 4.0 licence. No personal data were collected from anyone, no human subjects took part and everything runs locally, so no data leave the machine. Sex and race appear as model inputs only because they are part of the standard Folktables tasks; the project makes no decisions about individuals.

## Expected Outcomes / Deliverables {#sec:deliverables}

The project set out to deliver a Python package covering every stage of the pipeline, an interactive dashboard, an injection benchmark with held-out drift mechanisms, an evaluation on four real datasets with documented changes, a research paper and this report. All six were delivered (Chapter @ch:results and Appendix I).
