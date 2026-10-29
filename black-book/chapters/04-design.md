# Proposed Design {#ch:design}

This chapter turns the requirements of Chapter @ch:req into a design. It starts from a block diagram of the whole system, breaks the system into modules, shows the main classes and the flow of data between them, presents the schedule the project followed and ends with the design decisions taken to keep the system economical in computation and labels.

## Block Diagram of the System {#sec:block}

The system is organized as a pipeline of stages, each answering one of the questions a monitoring team asks. Fig. @fig:block shows the stages and the data that pass between them.

![Block diagram of ResilientAI. Stage letters follow the order in which a production window is processed; dashed arrows carry optional or supporting data](block_diagram.png){#fig:block width=150}

**A. Inputs.** The system takes the deployed model, the labeled reference data it was built from, the unlabeled production windows and, optionally, a few hundred late labels for each window.

**B. Preparation.** The data are brought into a common form. Feature types are recorded, so that nominal codes such as an occupation code are never treated as numbers. Images are mapped to embeddings by a frozen pretrained network. The reference data are split into training, calibration and test parts.

**C. Detection and estimation.** Shift detectors compare each window with the calibration part, the accuracy is estimated from the model's confidence and the shifted features are located with per-feature tests.

**D. Drift type and cause.** The label-free stage of the diagnosis decides whether anything moved and whether a change in the class balance alone explains it. When no label-free test rejects and an audit is available, the audit stage decides between concept drift, label noise and no drift. Root cause analysis compares what the model relies on before and after the shift.

**E and F. Acting on the findings.** The reliability stage scores the risk of each single prediction and the remediation triage advises whether a cheap retrain would recover the accuracy.

Every result of a study is written to one report in JavaScript Object Notation (JSON). The dashboard reads these reports and so does the build that generates the tables, figures and numbers of the paper and of this report.

## Modular Design of the System {#sec:modules}

The implementation is a Python package of \res{bb-src-modules} modules and \res{bb-src-lines} lines in \res{bb-src-packages} subpackages, plus the dashboard and the build scripts. Fig. @fig:modules shows the packages as layers, where each layer uses the layers below it.

![Packages of the implementation, arranged in layers; each layer uses the layers below it](module_diagram.png){#fig:modules width=150}

The foundation layer holds the data container and base classes (core), the statistical routines shared by every test (stats), the data loaders and validators (data) and the image networks (extractors). The analysis layer holds one package per stage of the block diagram. The orchestration layer runs studies on real data (experiments) and on injected drift (benchmark) and reads the run configuration (config). The presentation layer is the dashboard and the build of the paper. Table @tab:modules gives the responsibility, inputs and outputs of each package.

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

The detailed design covers the main classes and their relations, the flow of data from the public datasets to the dashboard and this report, the structure of the reports and the statistical design that every decision follows.

### Class Design {#sec:classes}

Fig. @fig:classes shows the main classes and functions in the notation of a class diagram.

![Main classes and functions. Hollow triangles mark inheritance, diamonds mark composition and dashed arrows mark use or return values](class_diagram.png){#fig:classes width=150}

`Dataset` is the common currency of the package: it holds the features, the optional target, the model's predictions and probabilities and the list of nominal features. Every detector extends `BaseDriftDetector`, so each offers `fit` on the reference data and `detect` on a window and returns a `DetectionResult` with its p value and statistic. `DriftPipeline` combines a detector with an optional localizer and root cause analyzer and returns a `PipelineResult`. The diagnosis is written as plain functions rather than classes, because each step is a stateless test: `label_free_diagnosis` and `audit_diagnosis` return their evidence and `combine` turns it into a `Diagnosis` with a drift type, the stage that decided it and a rationale. `ReliabilityAnalyzer` and `remediation_triage` act on single predictions and on the decision to retrain.

### Data Flow {#sec:dataflow}

Fig. @fig:dataflow shows how data move from the public sources to the outputs of the project.

![Flow of data from the public datasets to the dashboard, the paper and this report](dataflow.png){#fig:dataflow width=105}

Loaders download the public datasets once, cache them and give every feature its type. The study scripts and the injection benchmark run the pipeline and write one JSON report per study. The dashboard reads these reports directly. A separate build script turns the same reports into a file of named result values, the tables and the figures that the paper and this report use, so that no number is ever typed by hand. If a study is run again, every number in the documents changes with it.

### Report Structure

Each study report has four parts: the run configuration, a description of the reference data, the fitted reliability model and one record per window. A window record holds the window's size and accuracy, the result of every detector, the localization and root cause analysis, the accuracy estimates with their errors, the diagnosis with its evidence, a sample of reliability records and the time each stage took. Benchmark reports hold one record per injected window with the true drift type and intensity, so that every method can be graded on the same windows. The full schema is documented with the code in the project repository.

### Statistical Design

Every decision in the system is a hypothesis test at the significance level α = \res{acs-alpha}, with one exception: the population stability index raises an alarm at its conventional threshold of \res{acs-psi-threshold}. Where many tests are made together, for example one per feature, the chance of at least one false alarm is held at α by the Holm procedure [@holm1979], its weighted form or the Bonferroni bound. The diagnosis has two stages, each tested at α, so a window without drift receives a drift verdict with probability at most 2α. Fixing these rates before the data are seen is what lets a monitoring team trust an alarm. Chapter @ch:impl gives the tests themselves.

## Project Scheduling and Tracking {#sec:schedule}

The project ran over two semesters: Capstone Project I in the spring semester of 2026 and Capstone Project II in the autumn semester. Fig. @fig:gantt shows the timeline. The end of each phase is taken from the commit history of the code and paper repositories and its start is the team's estimate.

![Timeline of the project. Bars show the phases, dashed lines the main milestones and the gray band the semester break](gantt.png){#fig:gantt width=160}

The first semester produced a working prototype: detection with root cause analysis and a first dashboard, then geographic drift and the image pipeline on CLEAR-10. The second semester turned the prototype into a research system. The dashboard was rebuilt as a step-by-step story with the reliability layer and the injection benchmark was added. In October the diagnosis was redesigned around hypothesis tests with a stated error rate, a second model family, held-out drift mechanisms and the gas sensor data were added and the paper was written. Table @tab:milestones compares the milestones with the review schedule.

Table: Milestones, planned dates and dates achieved {#tab:milestones widths=3.4,1.6,1.6,2.4 size=9.5}
| Milestone | Planned | Achieved | Evidence |
|---|---|---|---|
| Problem statement and literature survey approved | [[review date]] | February 2026 | Synopsis, review sheet 1 |
| Working prototype with dashboard | [[review date]] | 20 February 2026 | First commit of the code repository |
| Image pipeline (CLEAR-10) | [[review date]] | 25 March 2026 | Commit history |
| Injection benchmark | [[review date]] | 8 September 2026 | Commit history |
| Error-controlled diagnosis, held-out benchmark, final results | [[review date]] | 16 October 2026 | Commit history; results regenerated |
| Research paper submitted | [[review date]] | [[submission date]] | Submission record (Appendix I) |
| Black book and final presentation | [[review date]] | [[final review date]] | This report |

The largest deviation from a steady plan is the gap between March and August, when no commits were made during the semester break and examinations. The October redesign was also not planned at the start: a review of the first diagnosis showed that its false alarm rate was not controlled and fixing it properly took most of the month. A later code review found two further errors, one in the error control of the label-free stage and one in how the audit counted nominal categories. Both were fixed without looking at the results and every result was produced again, which changed the verdict in \res{fix-nchanged} of the \res{fix-nwindows} benchmark windows.

## Sustainability-by-Design Decisions {#sec:sustain-design}

Several decisions in the design reduce computation, labeling effort or risk and so serve the efficiency target of SDG 12 described in Section @sec:sdg.

- **Labels only where they are needed.** The label-free stage settles most windows. Labels are asked for only in an audit of \res{acs-audit-n} rows and only when no label-free test rejects and the audit-size study (Section @sec:graphs) shows that more labels add little.
- **Advice before retraining.** The triage predicts whether a cheap retrain will help before any retraining is done, so a team does not spend computation on a retrain that cannot recover the loss.
- **Frozen networks and cached embeddings.** Images are embedded once by a frozen pretrained network and the embeddings are cached and reused by every test; no network is trained on the image stream.
- **Light models and tests.** The monitored models are logistic regression and histogram gradient boosting and the tests are classical statistics, so the whole system runs on a desktop processor.
- **Capped parallelism.** Long runs use a fixed number of workers and one heavy job at a time, which keeps power draw and the risk of a failed run low.
- **Explanations with a cost limit.** Shapley values are computed for a sample of rows against a small background set and only for the model where they are fast to compute.
- **Results generated once.** Every number in the paper and this report is generated from the stored study outputs, so documents can be rebuilt without rerunning experiments.
- **Privacy by design.** All processing is local and uses public data, so no personal data are collected or moved.
