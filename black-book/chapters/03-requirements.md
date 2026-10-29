# Requirement Gathering for the Proposed System {#ch:req}

A monitoring system is useful only if it answers the questions its users actually ask and does so within limits they can accept. This chapter describes how the requirements of ResilientAI were gathered, lists the functional and non-functional requirements that the rest of the report traces and records the hardware, software and constraints of the project.

## Introduction to Requirement Gathering {#sec:req-intro}

The requirements came from four sources. The literature survey of Chapter @ch:lit showed what existing tools already do and where they stop. The documentation of monitoring libraries and the patents of Section @sec:patents showed what industry monitors report. The mentor reviews of the project, held at each stage, turned a broad idea into testable targets and pushed us to state an error rate for every decision. Finally, building early prototypes and showing them as a dashboard exposed what a person needs to see before acting on an alarm.

Three groups of stakeholders shape the requirements. Machine learning engineers register a model with its reference data, run the monitor and export its reports. Monitoring teams read the results: they want to know whether the model is still accurate, what changed and what to do about it. Labeling teams supply the small audit of late labels when it is requested. The people affected by the model's decisions are indirect stakeholders whose interest is that a failing model is caught early. Fig. @fig:usecase shows the main use cases of the three direct groups.

![Use cases of ResilientAI for its three groups of direct users](usecase.png){#fig:usecase width=95}

The machine learning engineer sets the system up and runs it. The monitoring team reads alarms, accuracy estimates and shifted features, reads the drift type with the reason the system gives for it, checks doubtful predictions and decides on retraining. The labeling team only provides audit labels. The scope of the requirements follows from the problem definition of Section @sec:problem: tabular and image classifiers, batch windows of production data and a label budget of a few hundred rows per window.

## Functional Requirements {#sec:fr}

Table @tab:fr lists the functional requirements. Each has an identifier that the test cases of Chapter @ch:testing refer to, a priority and the module of the implementation that meets it.

Table: Functional requirements {#tab:fr widths=0.9,4.6,1.1,1.8 size=9.5}
| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-01 | Load a deployed model, labeled reference data and unlabeled production windows; validate their schema and record which features are nominal. | High | data, core |
| FR-02 | Split the reference data into disjoint training, calibration and test parts, stratified by class. | High | experiments |
| FR-03 | Map images to embeddings with a frozen pretrained network so that image data can be tested like tabular data. | Medium | extractors, data |
| FR-04 | Test each window for a change in the inputs and in the model outputs (Kolmogorov–Smirnov, population stability index, maximum mean discrepancy, confidence test) with a stated significance level. | High | detectors |
| FR-05 | Estimate the accuracy of the model on each window without labels (confidence-based performance estimation; average confidence, difference of confidences and thresholded confidence for comparison). | High | estimation, detectors |
| FR-06 | Locate the shifted features with a per-feature test and an effect size and report categories never seen in the reference. | High | localizers |
| FR-07 | Name the drift type as no drift, covariate shift, prior shift, concept drift or label noise, with the stage and the reason for the verdict, holding the family-wise error rate at the chosen level. | High | diagnosis |
| FR-08 | Use an optional audit of late labels to test for an accuracy drop and for errors that depend on a feature beyond the model's confidence. | High | diagnosis |
| FR-09 | Explain a shift by the change in what the model relies on: Shapley values for tabular models and class activation maps for image models. | Medium | rca |
| FR-10 | Score the risk of error of every single prediction from its confidence, its instability under small perturbations and an out-of-distribution score. | Medium | reliability |
| FR-11 | Advise whether a cheap retrain would recover accuracy, using importance weighting and, where available, an earlier labeled window. | Medium | remediation |
| FR-12 | Write every result of a study to one machine-readable report. | High | experiments |
| FR-13 | Present the results step by step in an interactive dashboard for real and injected drift. | High | dashboard |
| FR-14 | Inject drift of a known type and intensity into real data and grade the diagnosis against the truth. | High | benchmark |

## Non-Functional Requirements {#sec:nfr}

Table @tab:nfr gives the non-functional requirements as measurable targets, together with the way each was checked and the value achieved.

Table: Non-functional requirements, their targets and the values achieved {#tab:nfr widths=0.9,1.5,2.8,2.4,1.9 size=9.5}
| ID | Quality | Target | How checked | Achieved |
|---|---|---|---|---|
| NFR-01 | Reliability of alarms | Each detector's false alarm rate on windows without drift at or below α = \res{acs-alpha} | 95% CI over \res{det-ncontrols} benchmark control windows | Every CI contains α or lies below it |
| NFR-02 | Reliability of the diagnosis | Probability of a drift verdict on a window without drift at most 2α = \res{diag-fa-bound-pct}% | Benchmark control windows | \res{diag-fa-pct}% |
| NFR-03 | Error control | Family-wise error of the label-free decisions at most α | Simulation with \res{bb-fwer-reps} replicates | \res{fwer-wholm-pct}% |
| NFR-04 | Performance | Analysis of one window well within a daily monitoring cycle | Measured run time per window | At most \res{bb-time-max} s |
| NFR-05 | Label economy | Labels needed only for the optional audit | Design; audit-size study | \res{acs-audit-n} labels per window |
| NFR-06 | Reproducibility | Every result repeatable exactly | Seeded randomness; all reported numbers generated from the study outputs | Met |
| NFR-07 | Correctness of the code | All automated tests pass | pytest | \res{bb-tests-total} of \res{bb-tests-total} passed |
| NFR-08 | Usability | Each dashboard step answers one stated question with a plain-language summary | Review of the dashboard | Met (Section @sec:ui) |
| NFR-09 | Maintainability | Modules separated by responsibility, typed configuration, documented data contracts | Code structure (Section @sec:modules) | Met |
| NFR-10 | Privacy and security | No personal data collected; all processing local | Design; datasets are public | Met |
| NFR-11 | Resource use | No overload of the workstation during long runs | Capped workers; one heavy job at a time | Met |

## Hardware, Software, Technologies and Tools Utilized {#sec:tools}

Table @tab:tools lists the hardware and software used to build and run the system, with the versions installed when the results in this report were produced.

Table: Hardware, software, technologies and tools {#tab:tools widths=1.6,3.2,3.2 size=9.5}
| Category | Tool / specification | Purpose / version |
|---|---|---|
| Hardware | Intel Core i5-14600K (\res{const-cpu-cores} threads), 32 GB memory, NVIDIA GeForce RTX 4070 (12 GB) | Development, experiments, image embeddings on the graphics card |
| Software / OS | Linux (Arch-based distribution, kernel 7.2); Python 3.14 | Operating system and language |
| Languages / frameworks | NumPy 2.4, pandas 2.3, SciPy 1.17, scikit-learn 1.8 | Data handling, statistical tests, models |
| Languages / frameworks | PyTorch 2.11, torchvision 0.26, OpenCLIP 3.3 | Image network (ResNet-18), CLIP concept probe |
| Languages / frameworks | SHAP 0.50 | Shapley value explanations |
| Database / cloud / APIs | JSON files, one per study; Folktables 0.0.12 for the census data; no cloud services | Storage of results and data access |
| Visualization / UI | Streamlit 1.54, Plotly 6.5, Matplotlib 3.10, Graphviz | Dashboard and figures |
| Testing / analytics / version control | pytest 9.0, Git with two repositories (code and paper) | Automated tests and version control |
| Documentation | LibreOffice 26.8, Markdown sources | This report and the paper versions |

## Constraints {#sec:constraints}

The project worked within the following constraints and assumptions.

- **Labels.** Production labels are assumed to arrive late and to be expensive, so they may be used only in a small audit. The audit is assumed to be a random sample of the window.
- **Data.** Only public datasets could be used. Their drift types are not known exactly, which is why an injection benchmark was needed. The 2020 release of the American Community Survey has no standard version, so 2020 is missing from the timelines.
- **Models.** The system watches the model from outside: it needs predictions and class probabilities, not the internals of the model, except for the explanations.
- **Compute and time.** All work had to run on one workstation within the semester. Long benchmark runs were scheduled one at a time with capped parallel workers.
- **Batch setting.** Windows are batches of hundreds to thousands of rows. The tests are not designed for streams that need a verdict every few seconds.
- **Ethics and privacy.** No personal data could be collected and the sensitive attributes in the census tasks are used only as model inputs of standard public tasks.
