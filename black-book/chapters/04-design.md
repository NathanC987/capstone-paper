# Proposed Design {#ch:design}

This chapter turns the requirements of Chapter @ch:req into a design: the block diagram, the modules, the main classes and the flow of data, the schedule and the design decisions that keep the system economical.

## Block Diagram of the System {#sec:block}

The system is organized as a pipeline of stages, each answering one of the questions a monitoring team asks. Fig. @fig:block shows the stages and the data that pass between them.

![Block diagram of ResilientAI](block_diagram.png){#fig:block width=130}

Stage letters follow the order in which a production window is processed and dashed arrows carry optional or supporting data. **A. Inputs.** The system takes the deployed model, the labeled reference data it was built from, the unlabeled production windows and, optionally, a few hundred late labels for each window.

**B. Preparation.** The data are brought into a common form. Feature types are recorded, so that nominal codes such as an occupation code are never treated as numbers. Images are mapped to embeddings by a frozen pretrained network. The reference data are split into training, calibration and test parts.

**C. Detection and estimation.** Shift detectors compare each window with the calibration part, the accuracy is estimated from the model's confidence and the shifted features are located with per-feature tests.

**D. Drift type and cause.** The label-free stage of the diagnosis decides whether anything moved and whether a change in the class balance alone explains it. When no label-free test rejects and an audit is available, the audit stage decides between concept drift, label noise and no drift. Root cause analysis compares what the model relies on before and after the shift.

**E and F. Acting on the findings.** The reliability stage scores the risk of each single prediction and the remediation triage advises whether a cheap retrain would recover the accuracy.

Every result of a study is written to one report in JavaScript Object Notation (JSON). The dashboard reads these reports and so does the build that generates the tables, figures and numbers of the paper and of this report.

## Modular Design of the System {#sec:modules}

The implementation is a Python package of \res{bb-src-modules} modules and \res{bb-src-lines} lines in \res{bb-src-packages} subpackages, plus the dashboard and the build scripts. Fig. @fig:modules shows the packages as layers, where each layer uses the layers below it.

![Module diagram](module_diagram.png){#fig:modules width=130}

The foundation layer holds the shared data container, statistics and loaders, the analysis layer one package per stage of the block diagram, the orchestration layer the studies and the benchmark and the presentation layer the dashboard. Table @tab:modules gives the responsibility, inputs and outputs of each package.

Table: Responsibilities, inputs and outputs of the packages {#tab:modules widths=1.4,3.0,2.1,2.1 size=9.5}
| Package | Responsibility | Inputs | Outputs |
|---|---|---|---|
| core | Dataset container with feature types; base classes for detectors, localizers and root cause analyzers; the detection pipeline; result records | Arrays or data frames, model outputs | Dataset objects, pipeline results |
| data | Loading and caching of the census, gas sensor and image data; schema validation; image tabularization | Raw files, Folktables downloads | Typed tables, embedding tables |
| extractors | Frozen ResNet-18 and CLIP image networks | Images | 512-dimensional embeddings |
| stats | Holm and weighted Holm procedures, chi-square homogeneity, weighted Kolmogorov–Smirnov, Wilson intervals, Kish effective sample size | p values, samples, weights | Test results, intervals |
| detectors | Kolmogorov–Smirnov, population stability index, maximum mean discrepancy, confidence test, black-box shift detection, domain classifier | Reference and window data | Detection results with p values |
| estimation | Accuracy estimates from confidence: CBPE, average confidence, difference of confidences, thresholded confidence | Calibration and window probabilities | Estimated accuracy |
| localizers | Per-feature tests with effect sizes and unseen categories | Reference and window data | Ranked shifted features |
| diagnosis | Label-free stage, audit stage, combination into a verdict; rule baselines and the meta-classifier | Test p values, predictions, audit labels | Drift type, stage, rationale |
| rca | SHAP comparison for tabular models, class activation maps and a CLIP concept probe for images | Model, reference and window data | Attribution changes, heat maps |
| reliability | Per-prediction signals, out-of-distribution score, learned fusion | Calibration and window data | Risk score per prediction |
| remediation | Repair strategies and the label-free triage | Reference data, window data, earlier labels | Recommendation, predicted gain |
| benchmark | Drift injectors, window construction, grading metrics | Reference data, design, seed | Graded benchmark windows |
| experiments | Studies on ACS, gas sensor and CLEAR-10 data | Data, configuration | One JSON report per study |
| dashboard | Streamlit application, charts and generated plain-language notes | JSON reports | Interactive pages |

## Detailed Design {#sec:detailed}

The detailed design covers the main classes, the flow of data and the statistical design that every decision follows.

### Class Design {#sec:classes}

Fig. @fig:classes shows the main classes and functions in the notation of a class diagram.

![Class diagram](class_diagram.png){#fig:classes width=125}

Hollow triangles mark inheritance, diamonds mark composition and dashed arrows mark use or return values. `Dataset` is the common currency of the package: it holds the features, the optional target, the model's predictions and probabilities and the list of nominal features. Every detector extends `BaseDriftDetector`, so each offers `fit` on the reference data and `detect` on a window and returns a `DetectionResult` with its p value and statistic. `DriftPipeline` combines a detector with an optional localizer and root cause analyzer and returns a `PipelineResult`. The diagnosis is written as plain functions rather than classes, because each step is a stateless test: `label_free_diagnosis` and `audit_diagnosis` return their evidence and `combine` turns it into a `Diagnosis` with a drift type, the stage that decided it and a rationale. `ReliabilityAnalyzer` and `remediation_triage` act on single predictions and on the decision to retrain.

### Data Flow {#sec:dataflow}

Fig. @fig:dataflow shows how data move from the public sources to the outputs of the project.

![Data flow diagram](dataflow.png){#fig:dataflow width=105}

Loaders download and cache the public datasets, the study scripts and the benchmark write one JSON report per study and the dashboard reads these reports. A build script turns the same reports into the result values, tables and figures of the paper and this report, so that no number is typed by hand.

### Statistical Design

Every decision in the system is a hypothesis test at the significance level α = \res{acs-alpha}, with one exception: the population stability index raises an alarm at its conventional threshold of \res{acs-psi-threshold}. Where many tests are made together, for example one per feature, the chance of at least one false alarm is held at α by the Holm procedure [@holm1979], its weighted form or the Bonferroni bound. The diagnosis has two stages, each tested at α, so a window without drift receives a drift verdict with probability at most 2α. Chapter @ch:impl gives the tests themselves.

## Project Scheduling and Tracking {#sec:schedule}

The project ran over two semesters: Capstone Project I in the spring semester of 2026 and Capstone Project II in the autumn semester. Fig. @fig:gantt shows the timeline. The end of each phase is taken from the commit history of the code and paper repositories and its start is the team's estimate.

![Gantt chart of the project](gantt.png){#fig:gantt width=160}

Bars show the phases, dashed lines the milestones (the two progress reviews among them) and the gray band the semester break. The first semester produced a working prototype: detection with root cause analysis and a first dashboard, then geographic drift and the image pipeline on CLEAR-10. The second semester turned the prototype into a research system. The dashboard was rebuilt as a step-by-step story with the reliability layer and the injection benchmark was added. In October the diagnosis was redesigned around hypothesis tests with a stated error rate, a second model family, held-out drift mechanisms and the gas sensor data were added and the paper was written. Table @tab:milestones compares the milestones with the review schedule.

Table: Milestones, planned dates and dates achieved {#tab:milestones widths=3.4,1.6,1.6,2.4 size=9.5}
| Milestone | Planned | Achieved | Evidence |
|---|---|---|---|
| Problem statement and literature survey approved | 13 February 2026 | 19 February 2026 | Synopsis |
| Working prototype with dashboard | 27 February 2026 | 20 February 2026 | First commit of the code repository |
| Image pipeline (CLEAR-10) | 31 March 2026 | 25 March 2026 | Commit history |
| Progress review 1 | 3 September 2026 | 3 September 2026 | Review sheet 1 (Appendix I) |
| Injection benchmark | 4 September 2026 | 8 September 2026 | Commit history |
| Error-controlled diagnosis, held-out benchmark, final results | 9 October 2026 | 16 October 2026 | Commit history; results regenerated |
| Research paper submitted to ICMMDU 2026 | 25 October 2026 | 24 October 2026 | Submission record |
| Paper accepted at ICMMDU 2026 | 31 October 2026 | 27 October 2026 | Acceptance mail (Appendix I) |
| Progress review 2 | 4 November 2026 | 4 November 2026 | Review sheet 2 (Appendix I) |
| Black book and final presentation | 27 November 2026 | 20 November 2026 | This report |

The largest deviation from a steady plan is the gap between March and August, when no commits were made during the semester break and examinations. The October redesign was not planned at the start: a review of the first diagnosis showed that its false alarm rate was not controlled and fixing it took most of the month. The paper was accepted three days after its submission, four days ahead of plan.

## Sustainability-by-Design Decisions {#sec:sustain-design}

Several decisions in the design reduce computation, labeling effort or risk and so serve the efficiency target of SDG 12 described in Section @sec:sdg.

- **Labels only where they are needed.** Labels are asked for only in an audit of \res{acs-audit-n} rows and only when no label-free test rejects.
- **Advice before retraining.** The triage predicts whether a cheap retrain will help before any retraining is done, so a team does not spend computation on a retrain that cannot recover the loss.
- **Light computation.** Images are embedded once by a frozen network and the embeddings are cached, the models and tests are classical and long runs use capped parallel workers, so the whole system runs on a desktop processor.
- **Privacy by design.** All processing is local and uses public data, so no personal data are collected or moved.
