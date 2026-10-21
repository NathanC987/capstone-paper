---
title: Supplementary Material for "Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models"
author: Sanjay Mirchandani; 1*
author: Nathan Cherian; 1
author: Rahul Guhagarkar; 1
author: Alok Pal; 1
author: Akul Patre; 1
affiliation: 1; Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: sanjay.mirchandani@ves.ac.in
note: Section, figure, table and equation numbers without the prefix S refer to the main paper.
---

# Datasets {#sec:datasets}

Each of the four datasets contains drift with a documented cause, so the verdicts of the pipeline can be checked against known events. Table @tab:datasets summarizes them. The two census tasks use data from California (CA), Texas (TX), New York (NY), Florida (FL) and Washington (WA).

Table: Datasets, drift windows and reference accuracy. Rows gives the smallest and largest window, Inputs the number of features or embedding dimensions and the last two columns the reference test accuracy of logistic regression (LR) and gradient boosting (GB) {#tab:datasets}
<<gen:tab_datasets>>

*ACS Income and ACS Employment.* Both tasks come from the American Community Survey (ACS) of the United States Census Bureau, as packaged by Folktables [@ding2021retiring]. ACS Income predicts whether a person earns more than \$50,000 from \res{inc-nfeatures} features. ACS Employment predicts, from \res{emp-nfeatures} features, whether a person aged 16 to 90 is employed. Nominal features, such as an occupation code, are treated as categorical because their numeric order carries no meaning. There is no standard 2020 release [@census2021experimental]. In 2019 the relationship variable RELP was replaced by RELSHIPP [@census2019pums], which we map back to RELP using the code labels of the 2018 and 2019 data dictionaries. For GB, nominal codes beyond the 254 most frequent are pooled, which is the limit of the implementation.

*Gas sensor array drift.* This dataset from the University of California, Irvine (UCI) machine learning repository holds 13,910 measurements of six gases by 16 metal oxide sensors over 36 months, in ten batches [@vergara2012gas; @rodriguezlujan2014gas]. Each measurement has eight features per sensor. Batches 1 and 2 form the reference and batches 3 to 10 the windows. Because some batches are small, the number of audit labels for a window of $n$ rows is given by $\min(600,\lfloor n/2\rfloor)$.

*CLEAR-10.* This image stream holds ten object classes and a background class in ten time-ordered buckets of about 3,300 images each [@lin2021clear]. Bucket 1 serves as the reference. Both models operate on the frozen ResNet-18 embeddings.

# Injection benchmark {#sec:benchmark}

The benchmark uses the 2014 data of \res{bench-nstates} states (\res{bench-states}) for both ACS tasks. Each state is a reference distribution with its own model, split as in Section @m:sec:detection. For each of \res{bench-nseeds} seeds the split, the window and the injection are redrawn, which gives \res{bench-nreps} replicates per configuration. Each replicate draws a production window of \res{bench-prodsize} rows and a grading holdout of \res{bench-holdsize} rows from the test part. Each mechanism is injected into both at three intensities.

*Design A* injects the four types in ways that partly match the tests. Covariate shift rescales two numeric features (ACS Income: \res{bench-cov-features-inc}) for a random subset of rows. Prior shift drops rows of one class until the positive rate rises by \res{bench-prior-steps}. Concept drift inverts the labels of the \res{bench-concept-steps}% of rows with the highest value of one feature (ACS Income: \res{bench-concept-feature-inc}). Label noise flips a random \res{bench-noise-steps}% of labels. Each replicate also includes a control window without drift.

*Design B* uses mechanisms that the tests were not designed for. Covariate shift is selection bias: each row is kept with a probability given by $\sigma(\beta s(x))$, where $\sigma$ is the logistic function, $s$ is a seeded random score over all inputs and $\beta\in\{\res{bench-b-betas}\}$. The rows stay real and $P(Y\mid X)$ is exactly unchanged. Prior shift lowers the positive rate by \res{bench-b-prior-steps}. Concept drift inverts the labels in the top \res{bench-b-concept-steps}% of a second random score, which defines an oblique region that no single feature describes. For ACS Income a second concept drift raises the income threshold to \res{bench-b-thresholds}. Label noise is class-conditional, with positive labels flipped to negative at rates of \res{bench-b-noise-steps}%.

The learned meta-classifier of Section @m:sec:baselines uses nine statistics of each window: the evidence $-\log_{10}p$ of each block test, the share of features with residual shift, the BBSE prior change, the CBPE change, the evidence and size of the audit accuracy drop and the evidence of the error structure test. Replicates are the unit of analysis in the paired tests because the windows of one replicate share a model and a reference.

# Methods and ablations {#sec:methods}

Table @tab:methods repeats Table @m:tab:methods of the paper with the three ablations of our procedure added.

Table: Share of benchmark windows with the correct drift type (%), including the ablations. Inc. and Emp. denote ACS Income and ACS Employment, A and B the two designs. An arrow marks a significant difference from ours after Holm correction: down means ours is better, up means ours is worse {#tab:methods}
<<gen:tab_methods>>

Removing the MMD block changes little on the benchmark, whose shifts are visible feature by feature. Removing the confidence term from the audit null lowers the accuracy on design A, because uniform label noise then looks like concept drift. Replacing the confidence bins by cells of predicted class and confidence helps on design B but not on ACS Income design A.

# Held-out mechanisms {#sec:mechanisms}

Table @tab:mechanisms breaks the design B results down by mechanism.

Table: Design B results by drift mechanism. Corr. is the share of windows typed correctly (%) and Drop the mean true accuracy drop in points, where a negative value means that accuracy rose. The income threshold mechanism exists only for ACS Income {#tab:mechanisms}
<<gen:tab_mechanisms>>

Three mechanisms transfer well: selection bias, a lower positive rate and concept drift in an oblique region. Raising the income threshold relabels some rows in every window but barely changes accuracy. Because the audit first asks whether accuracy fell, it reports no drift in most of these windows; the procedure is designed to find drift that harms the model, which this drift does not. Class-conditional label noise is the hardest mechanism. This is a genuine limitation of a null model that conditions on confidence alone.

\newpage

The audit size controls how well the audit stage separates concept drift from label noise. Fig. @fig:budget shows the share of correctly diagnosed windows on ACS Income design A with LR as the number of audit labels grows.

![Share of correctly diagnosed windows on ACS Income design A with LR against the number of audit labels. The shaded bands are 95% Wilson intervals](FigS1.png){#fig:budget width=83.5}

Concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows with 200 labels and \res{b-inc-a-lr-budget-concept-600}% with 600, while label noise is identified in \res{b-inc-a-lr-budget-labelnoise-200}% and \res{b-inc-a-lr-budget-labelnoise-600}%. The 600 labels used throughout the paper thus lie where the gain from more labels has largely flattened.

# Detection and accuracy estimation {#sec:detection}

Table @tab:detectors gives the alarm rate of each detector by injected type, pooled over the four design A configurations.

Table: Detector alarm rates on design A by injected type. The no drift column is the false alarm rate with its 95% confidence interval (CI) {#tab:detectors}
<<gen:tab_detectors>>

Over \res{det-ncontrols} control windows every interval contains $\alpha=\res{acs-alpha}$ or lies below it. Every detector catches covariate shift and all except PSI also catch most prior shifts. Concept drift and label noise windows share their inputs with the control window of their replicate, so no detector can see them, which is why the audit is needed.

The accuracy estimates are compared by their mean absolute error. On design A the errors of CBPE, AC, DoC and ATC stay below \res{est-bench-none-max} points without drift and below \res{est-bench-covariate-max} under covariate shift. Under concept drift and label noise every error equals the whole loss, about \res{est-bench-conceptnoise-cbpe} points, because the inputs do not change. On the gas sensor data all four are off by \res{est-gas-best} to \res{est-gas-worst} points on average. In batch 8 the LR model's mean confidence falls from \res{gas-ref-conf} to \res{gas-b8-conf} and its accuracy to \res{gas-b8-acc}, yet CBPE estimates \res{gas-b8-est}.

\newpage

# Real drift {#sec:real}

Table @tab:income gives the details behind the ACS Income panel of Fig. @m:fig:timelines.

Table: Detection and diagnosis on the ACS Income windows. Δ is the accuracy change in points and Est. err. the error of the CBPE estimate. A tick marks an alarm; Conf. denotes the confidence test, DC the domain classifier and Cov. a covariate verdict. Top shifts lists the two features with the largest effect size: occupation (OCCP), place of birth (POBP), relationship (RELP) and race (RAC1P) {#tab:income}
<<gen:tab_income>>

The control window raises no alarm with either model. CA 2015, whose accuracy did not change significantly, is diagnosed as no drift by both models, while every other window is diagnosed as covariate shift. When the occupation codes were revised in 2018 [@census2020occupation], the model's reliance on occupation fell (SHAP change \res{inc-ca2018-shap-occp}). From 2021 onwards race shifts, following the change in how the Census Bureau codes written race answers [@census2021race].

Every gas sensor batch is diagnosed as covariate shift. BBSE first labels these batches as prior shift because the predicted labels move, but the consistency test shows that they move because the sensors read differently, not because the mix of gases changed. On ACS Employment the inputs move, including relationship in 2019 and race from 2021, but the model is barely affected. On CLEAR-10 both models report no drift in buckets \res{clr-windownums-none} and covariate shift in buckets \res{clr-windownums-covariate}. In buckets \res{clr-windownums-mmdonly} no single embedding dimension shifts significantly with LR. Only the MMD test detects the change, while the predicted labels stay put.

For the reliability layer, the gas sensor calibration part contains too few wrong predictions (\res{rel-gas-lr-cal-errors} with LR and \res{rel-gas-hgb-cal-errors} with GB), so the risk falls back to confidence. On the benchmark the fused risk changes AUROC by \res{rel-bench-gain-min} to \res{rel-bench-gain-max} relative to confidence alone.

# Protocol and configuration {#sec:protocol}

All settings were fixed before the evaluation that uses them. The diagnosis and design B were both fixed before design B was first run. A later code review uncovered two errors in the diagnosis. The label-free stage had used a gatekeeping rule whose family-wise error rate reached \res{fwer-gate-pct}% at a nominal \res{fwer-alpha-pct}% in a simulation, compared with \res{fwer-wholm-pct}% for the weighted Holm procedure of Section @m:sec:diagnosis. The audit had also counted nominal categories over the reference and audit rows together. Both were corrected without regard to the results and every result was regenerated, which changed the verdict in \res{fix-nchanged} of the \res{fix-nwindows} benchmark windows.

Every permutation p value is given by $(1+b)/(1+B)$, where $b$ of the $B$ permutations reach the observed statistic [@phipson2010]. The confidence test pools sparse histogram cells until every expected count reaches \res{const-min-expected} [@cochran1954]. The weighted feature tests of the label-free stage use Kish's effective sample size [@kish1965]. The risk fusion of the reliability layer is fitted only when the calibration part holds at least ten wrong predictions per signal [@peduzzi1996]; otherwise the risk is simply $1-c$. Proportions carry Wilson intervals [@wilson1927] and means carry bootstrap intervals over replicates. Permutation tests use \res{acs-mmd-perm} permutations, SHAP explains \res{acs-shap-n} rows per side against \res{acs-shap-bg} background rows and each real audit uses \res{acs-audit-n} labels from its own random stream. SHAP is reported for LR only, because for GB the exact explainer would take hours per window. In the audit, a nominal category receives its own bin only if it occurs at least $n_{\min}$ times, where $n_{\min}$ is given by $\lceil 5/\min(e,1-e)\rceil$ and $e$ is the audit error rate; the remaining categories share one bin. The density ratio weights of the triage are fitted on separate folds and truncated at \res{const-weight-clip} times their mean. The importance-weighted holdout is \res{const-triage-valfrac}% of the reference. One workstation with a \res{const-cpu-cores}-core processor and a graphics processor ran everything; the graphics processor computed the embeddings, permutation tests and large audit fits in double precision, with p values identical to the processor code. The software was scikit-learn [@pedregosa2011scikit], SciPy, NumPy, SHAP, OpenCLIP and PyTorch.

# References {-}
