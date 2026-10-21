---
title: Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models
author: Sanjay Mirchandani; 1*
author: Nathan Cherian; 1
author: Rahul Guhagarkar; 1
author: Alok Pal; 1
author: Akul Patre; 1
affiliation: 1; Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: sanjay.mirchandani@ves.ac.in
keywords: concept drift, label shift, model monitoring, drift diagnosis, hypothesis testing
---

% Periodica Polytechnica EECS version. Every number is a \res{key} from
% paper/generated/results.tex; build with examples/paper/build_ppeecs.py.

::: abstract
A drift alarm reports that production data have changed. The appropriate response, however, depends on the type of change, which current monitoring tools rarely identify: covariate shift calls for reweighting, prior shift for recalibration and concept drift for new labels, while label noise points to the labeling process rather than to the model. We present an open monitoring pipeline that detects drift, estimates its cost in accuracy without labels, locates the shifted features, names the drift type, scores the reliability of individual predictions and advises whether a cheap retrain will help. Its core is a procedure that names the four drift types with a stated error rate. Established label-free tests separate covariate shift from prior shift, while a new test on a few hundred late labels separates concept drift from label noise by asking whether the errors have changed beyond what the model's confidence explains. On injected drift in two census tasks and two model families, the procedure identifies the type in \res{bench-a-ours-min} to \res{bench-a-ours-max}% of windows and outperforms rules used in monitoring practice. A learned classifier does better on the drift it was trained on but reaches only \res{bench-b-meta-min} to \res{bench-b-meta-max}% on held-out drift mechanisms, where our tests retain \res{bench-b-ours-min} to \res{bench-b-ours-max}%. On four real datasets with documented changes, the pipeline reported no drift on any control window and traced the known events.
:::

# Introduction {#sec:intro}

A deployed classifier can lose accuracy quietly as production data move away from the data it was trained on, often long before reliable labels reveal the loss [@rabanser2019failing]. Existing monitors are good at announcing that a distribution has changed [@rabanser2019failing] and at estimating how much accuracy has been lost [@garg2022atc; @kivimaki2025performance]. They rarely report what kind of change occurred, although each kind of drift calls for a different response.

The literature distinguishes three types of dataset shift [@moreno2012unifying]. Under covariate shift the inputs move while the rule linking inputs to labels stays the same, so reweighting the training data can help. Under prior shift only the class balance changes and recalibrating the model is usually enough. Concept drift alters the rule itself and needs fresh labels. We add label noise as a fourth type. It corrupts the labels used to judge the model and points to the labeling process rather than to the model.

Naming the type turns out to be harder than detecting a change. Covariate and prior shift both move the inputs and the predictions, whereas concept drift and label noise leave the inputs untouched and are therefore invisible to any label-free test.

We identify the type with a short sequence of hypothesis tests run at one significance level, with the family-wise error rate controlled. The first stage needs no labels and builds on established methods. It tests the inputs and the predictions for a shift, estimates the new class balance with black-box shift estimation (BBSE) [@lipton2018bbse] and, following Roschewitz et al. [@roschewitz2025shiftid], asks whether this balance alone explains the shift in the inputs (prior shift) or not (covariate shift). The second stage is new. Using a few hundred late labels, it asks whether accuracy has fallen and, if so, whether the errors have changed in a way that depends on some input feature. Uniform label noise changes the error rate only according to how confident the model is, whereas concept drift changes it within one region of the input space. Since every step is a formal test, the false alarm rate is fixed in advance.

The contributions are as follows.

1. An audit test that separates concept drift from label noise using only a few hundred late labels. Existing shift tests, such as DetectShift [@maiapolo2023detectshift], either require labeled production data or ignore label noise.
2. A hierarchical procedure that combines this audit with a label-free stage and names four drift types under family-wise error control.
3. A benchmark covering two tabular tasks and two model families, with matched as well as held-out drift mechanisms. It shows that tests built on the definitions of the types transfer to new drift, whereas a learned rule does not.
4. An open end-to-end monitoring pipeline that covers detection, accuracy estimation, root cause analysis, diagnosis, reliability scoring and remediation triage, evaluated on four real drifts with documented causes.

\noindent Section @sec:sota reviews related work and Section @sec:method describes the pipeline. Section @sec:setup sets out the experiments and Section @sec:results reports them. Section @sec:discussion discusses what the results mean and where they stop. Section @sec:conclusion concludes.

# State of the art {#sec:sota}

Table @tab:positioning compares our work with the closest existing methods: black-box shift detection (BBSD), BBSE, confidence-based performance estimation (CBPE), DetectShift and the method of Roschewitz et al. The paragraphs after it review what each group of related work offers a monitoring team and what it leaves open.

Table: Capabilities of the closest methods and of ours. A tick marks a capability that the method provides {#tab:positioning}
| Method | Error rate stated | Accuracy estimate | Localizes features | Types named | Concept vs noise | Held-out drift |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| BBSD [@rabanser2019failing] | ✓ | – | limited | – | – | – |
| BBSE [@lipton2018bbse] | ✓ | – | – | prior | – | – |
| CBPE [@kivimaki2025performance] | – | ✓ | – | – | – | – |
| DetectShift [@maiapolo2023detectshift] | ✓ | – | – | needs labels | – | – |
| Roschewitz et al. [@roschewitz2025shiftid] | ✓ | – | – | prior, cov. | – | – |
| Ours | ✓ | ✓ | ✓ | four | ✓ | ✓ |

*Drift types.* Moreno-Torres et al. [@moreno2012unifying] define covariate shift, prior shift and concept shift according to which part of the joint distribution of inputs and labels changes. DetectShift tests for a shift in this joint distribution and in each of its parts, $P(X)$, $P(Y)$, $P(X\mid Y)$ and $P(Y\mid X)$ [@maiapolo2023detectshift]. However, it requires labels for the new data, a limitation its authors acknowledge. We adopt the same definitions, add label noise as a fourth type and require labels only for a small audit.

*Drift detection.* Detectors that track the error rate, such as the drift detection method (DDM) [@gama2004ddm], need a label for every prediction. They can detect concept drift but cannot distinguish it from label noise. Label-free detectors instead compare the inputs or the model outputs. Rabanser et al. [@rabanser2019failing] compared univariate tests, kernel tests [@gretton2012kernel], classifier two-sample tests [@lopezpaz2017c2st] and BBSD applied to the model outputs. They found that BBSD worked best overall. All of them indicate that a shift has occurred but not of which type. Our pipeline uses such tests as building blocks and goes on to name the type.

*Label shift.* BBSE recovers the new class prior from the confusion matrix of any classifier [@lipton2018bbse]. It assumes that the inputs within each class do not change, which is precisely the assumption that separates prior shift from covariate shift. Roschewitz et al. [@roschewitz2025shiftid] test this assumption on medical images. They resample the reference data to the estimated prevalence and attribute the shift to prevalence if the features then no longer differ. Our label-free stage builds on the same idea but uses importance weights instead of resampling and places every label-free decision in one family with a stated error rate.

*Performance estimation without labels.* Average confidence (AC) [@hendrycks2017baseline], difference of confidences (DoC) [@guillory2021predicting], average thresholded confidence (ATC) [@garg2022atc] and CBPE [@kivimaki2025performance] all estimate accuracy from model outputs. Each assumes that the relationship between confidence and accuracy carries over to production. Because models often remain confident as their accuracy falls under shift [@ovadia2019trust], this assumption can fail. Our pipeline reports CBPE alongside the other three and treats it as an upper bound when the assumption breaks.

*Explanation, reliability and benchmarks.* Shapley additive explanations (SHAP) [@lundberg2017unified] and class activation maps (CAM) [@zhou2016cam] attribute predictions to features or to image regions. Out-of-distribution (OOD) scores such as the Isolation Forest [@liu2008isolation] flag unusual inputs, while importance weighting corrects covariate shift [@shimodaira2000; @sugiyama2007; @cortes2010weights]. Folktables [@ding2021retiring] and CLEAR [@lin2021clear] provide real shifts, although the type of each shift is unknown. Injected shifts supply a ground truth [@rabanser2019failing] but risk favoring the method under test. Each of these tools serves one stage of our pipeline. Our benchmark holds out drift mechanisms to limit that risk.

Each prior method thus addresses part of the problem. To our knowledge, no published method separates concept drift from label noise with a small label audit. Nor has any type diagnosis been evaluated on drift mechanisms held out from its design.

# Method {#sec:method}

The pipeline is designed for a team that has a deployed model, the labeled data on which it was built and a stream of unlabeled production data. Nothing else is required, although a few hundred late labels sharpen the diagnosis once they arrive. We first define the four drift types and then follow the data through the pipeline, whose stages Fig. @fig:architecture shows.

![Stages of the monitoring pipeline, from the inputs (A) to the advice on retraining (F)](Fig01.png){#fig:architecture width=81.6}

Stages A to C bring the data into a common form, test whether anything has changed and estimate how much accuracy the change may cost. Stage D, the core of this paper, names the type of change and points to its likely cause. Stages E and F turn these findings into action for individual predictions and for the retraining decision. Only the optional audit in stage D uses production labels. Apart from the population stability index (PSI), which alarms at its conventional threshold, every decision is a hypothesis test at the significance level $\alpha=\res{acs-alpha}$. The family-wise error rate is controlled by the Holm procedure [@holm1979], its weighted form or its Bonferroni bound.

## Notation and drift types {#sec:types}

The tests described below require a precise statement of what each type of drift changes. The reference data are drawn from a distribution $P(X,Y)$ over inputs $X$ and labels $Y$. A production window is a batch of rows from a later period or a different region, drawn from $Q(X,Y)$. The model returns a predicted label $\hat y$ and a confidence $c$, its largest class probability. The four types differ in what changes between $P$ and $Q$. Covariate shift has $Q(X)\neq P(X)$ while $Q(Y\mid X)=P(Y\mid X)$. Prior shift has $Q(Y)\neq P(Y)$ while $Q(X\mid Y)=P(X\mid Y)$. Concept drift has $Q(Y\mid X)\neq P(Y\mid X)$. Under label noise the true distribution stays the same, but each observed label differs from the true one with some probability. An audit is a random sample of $m$ production rows whose labels arrive late. A control window is drawn from the reference distribution itself and should therefore raise no alarm. Real drift can mix several types, as Section @sec:discussion discusses.

## Reference split, detection and estimation {#sec:detection}

Stage C addresses three questions in turn: whether the data have moved, how much accuracy the change might cost and where it is located. It first requires a clean reference. The labeled reference data are split into three disjoint parts, stratified by class: \res{acs-split-pct-train}% for training, \res{acs-split-pct-calibration}% for calibration and \res{acs-split-pct-test}% for testing. The model is fitted on the training part alone. The calibration part is the reference window for every detector and fits the accuracy estimator, while the test part gives the reference accuracy and acts as the control window. Nominal features, such as an occupation code, are treated as categorical because their numeric order carries no meaning. Images are mapped to the \res{clear-dim}-dimensional output of the global average pooling layer of a frozen residual network with 18 layers (ResNet-18) trained on ImageNet [@he2016deep], so image drift can be tested with the tabular tests [@rabanser2019failing].

Six detectors decide whether the inputs or the model outputs have moved. The Kolmogorov–Smirnov (KS) test is applied to each numeric feature with a Bonferroni correction. PSI alarms at the conventional value of \res{acs-psi-threshold} [@siddiqi2006]. The maximum mean discrepancy (MMD) test [@gretton2012kernel] is a permutation test on all standardized inputs jointly, using a Gaussian kernel. The confidence test compares histograms of $c$ with a $\chi^2$ test of homogeneity, pooling sparse cells until every expected count reaches \res{const-min-expected} [@cochran1954]. Two detectors from Rabanser et al. [@rabanser2019failing] serve as baselines. BBSD applies a KS test to each class probability. The domain classifier trains gradient boosted trees to separate \res{acs-dc-n} reference rows from as many production rows and compares its held-out accuracy with $1/2$ by an exact binomial test [@lopezpaz2017c2st]. Every permutation p value is given by $(1+b)/(1+B)$, where $b$ of the $B$ permutations reach the observed statistic [@phipson2010].

Because labels arrive late, accuracy is first estimated from the model's own confidence with CBPE [@kivimaki2025performance]. A map $a(\cdot)$ from confidence to the probability of a correct prediction is fitted by histogram binning on the calibration part. The estimate $\hat A$ for a window with confidences $c_1$ to $c_n$ is given by

$$\hat A = \frac{1}{n}\sum_{i=1}^{n} a(c_i)$$. {#eq:cbpe}

\noindent A confidence bin with fewer than \res{const-min-expected} calibration rows gives no reliable accuracy, so predictions in such a bin keep their own confidence in Eq. (@eq:cbpe). AC, DoC and ATC (with the negative entropy score) are fitted on the same calibration part as baselines [@hendrycks2017baseline; @guillory2021predicting; @garg2022atc].

An alarm is more useful when it also says where the change is located. Localization tests every feature with KS (numeric) or $\chi^2$ homogeneity (nominal) under Holm correction and reports an effect size in $[0,1]$, the KS statistic or Cramér's $V$. For nominal features it also reports the share of production rows whose category never occurs in the reference.

## Drift type diagnosis {#sec:diagnosis}

Stage D turns an alarm into one of the four types, each with its own response. It works in two stages along the decision path in Fig. @fig:decision, which the rest of this section explains. The upper row of questions uses no labels and separates covariate from prior shift. The lower row, which runs only when no label-free test rejects and an audit is available, separates concept drift from label noise.

![Decision path that names the drift type. Questions are shown in white boxes and verdicts in gray boxes; the upper row needs no labels and the lower row uses the audit](Fig02.png){#fig:decision width=83.5}

*Label-free stage.* The first question in Fig. @fig:decision is whether anything has moved at all. Three blocks of tests answer it: the feature tests, a $\chi^2$ test on the predicted labels and the MMD test. They form one family, tested at level $\alpha$ with a weighted Holm procedure [@holm1979]. The three blocks receive equal weight, which the feature block divides equally among its features. Whenever a test is rejected, its weight passes to the tests that remain, so the family-wise error rate is controlled over every label-free decision. The first step equals the Holm procedure over the three blocks, with each block's features pooled by their Bonferroni p value. Pooling lets the MMD test, whose smallest possible p value is $1/(B+1)$, compete with many feature tests. If no test rejects, the label-free stage reports no shift.

If a block rejects, the diagnosis asks whether a change in the class balance alone explains the shift. BBSE estimates the new class prior. Let $C_{jk}=P(\hat y=j,y=k)$ on the calibration part and let $\mu_j$ be the share of production predictions in class $j$. The class weights $w_k=Q(Y=k)/P(Y=k)$ are given by the solution of

$$C\,w = \mu$$. {#eq:bbse}

\noindent Under a pure prior shift the inputs within each class keep their distribution, so reweighting each reference row by the weight $w_{y}$ from Eq. (@eq:bbse) should reproduce the production inputs. This label shift consistency test follows the prevalence adjustment of Roschewitz et al. [@roschewitz2025shiftid]. The feature tests are repeated against the reweighted reference with Kish's effective sample size [@kish1965] and Holm correction. Any feature that still differs carries a covariate shift. If none differs and the predicted labels have moved, the shift is a prior shift. A prior shift always moves the predicted labels of an informative classifier, so a shift without such a move is called covariate.

*Audit stage.* Concept drift and label noise leave the inputs and the model outputs unchanged, so only labels can reveal them. The audit draws $m$ late labels and first checks with a one-sided two-proportion test whether accuracy has fallen. If it has, the diagnosis asks whether the change in errors depends on a feature. A logistic model of whether a prediction is correct is fitted on the calibration rows and the audit rows together. Its null form contains \res{const-quantile-bins} confidence bins at reference quantiles, bins of a feature $f$, an audit indicator and the interaction of that indicator with the confidence bins. The alternative adds the interaction of the audit indicator with the bins of $f$ and is compared with the null by a likelihood ratio test for each feature. A nominal category receives its own bin only if it occurs at least $n_{\min}$ times in the audit, where $n_{\min}$ is given by $\lceil 5/\min(e,1-e)\rceil$ and $e$ is the audit error rate. The remaining categories share one bin.

It is the confidence term that separates the two types. In a binary task, uniform label noise at rate $r$ makes the probability of a correct prediction equal to $r+(1-2r)\,q(x)$, where $q(x)$ is the model's own probability of being right at $x$. The change therefore depends on $x$ only through $q(x)$, which the confidence bins of the null absorb. Concept drift instead shifts the errors within a region of some feature. A feature that remains significant after Holm correction therefore indicates concept drift, whereas no significant feature indicates label noise. Because each of the two stages is tested at level $\alpha$, a window without drift receives a drift verdict with probability at most $2\alpha$.

## Root cause analysis {#sec:rca}

Knowing the type tells a team what to do, while root cause analysis tells it where to look. This step asks which inputs the model's decisions depend on differently after the shift. It narrows the search but does not prove a cause. For tabular models we compute SHAP values [@lundberg2017unified] of the deployed model with its preprocessing and compare the mean absolute attribution of each feature between reference and production rows. Each change carries a percentile bootstrap interval whose level is Bonferroni adjusted over the features. For images, CAM shows which image regions support the prediction of the linear head [@zhou2016cam].

## Reliability and remediation triage {#sec:triage}

The tests so far describe a window as a whole. Two practical questions remain: which individual predictions deserve less trust and whether a cheap retrain would recover the lost accuracy. For the first, each prediction receives three signals in $[0,1]$: the confidence risk $1-c$, an OOD score and its instability under small input perturbations. The OOD score combines an Isolation Forest [@liu2008isolation] with a standardized distance. A logistic regression fitted on the calibration part combines the three signals into a probability of error. It is fitted only when the calibration part holds at least ten wrong predictions per signal [@peduzzi1996]; otherwise the risk is simply $1-c$.

For the second, the triage predicts without production labels whether a cheap retrain will help. A classifier that separates reference from production rows provides density ratio weights, fitted on separate folds and truncated at \res{const-weight-clip} times their mean [@cortes2010weights]. A model trained with these weights is compared with an unweighted one on a held-out \res{const-triage-valfrac}% of the reference, itself weighted by the density ratio [@shimodaira2000; @sugiyama2007]. When late labels from an earlier window are available, a second probe retrains on them and is validated on a held-out part of that window. A retrain is recommended when a probe's predicted gain is significant after Holm correction across probes.

# Experimental setup {#sec:setup}

The experiments answer two questions. Does the procedure name the type correctly when the truth is known, including for drift it was not designed for? And does it behave sensibly on real drift, where the type is unknown but the causes are documented?

*Protocol.* All settings below were fixed before the evaluation that uses them. The diagnosis was frozen before the held-out design B was first run. A later code review uncovered two errors in the diagnosis. The label-free stage had used a gatekeeping rule whose family-wise error rate reached \res{fwer-gate-pct}% at a nominal \res{fwer-alpha-pct}% in a simulation, compared with \res{fwer-wholm-pct}% for the weighted Holm procedure of Section @sec:diagnosis. The audit had also counted nominal categories over the reference and audit rows together. Both were corrected without regard to the results and every result was regenerated, which changed the verdict in \res{fix-nchanged} of the \res{fix-nwindows} benchmark windows. Permutation tests use \res{acs-mmd-perm} permutations, SHAP explains \res{acs-shap-n} rows per side against \res{acs-shap-bg} background rows and each real audit uses \res{acs-audit-n} labels from its own random stream. All randomness is seeded, so every result repeats exactly. One workstation with a \res{const-cpu-cores}-core processor and a graphics processor ran everything. The software was scikit-learn [@pedregosa2011scikit], SciPy, NumPy, SHAP, OpenCLIP and PyTorch.

## Models

Since the procedure should not depend on one kind of model, the same pipeline monitors two untuned model families. The first is logistic regression (LR) with $L_2$ regularization ($C=1$) on standardized numeric and one-hot encoded nominal features. The second is histogram gradient boosting (GB) [@ke2017lightgbm] from scikit-learn [@pedregosa2011scikit] with default settings, no early stopping and native splits on nominal codes. Codes beyond the 254 most frequent are pooled, which is the limit of the implementation. For CLEAR-10 both models operate on the frozen embeddings. SHAP is reported for LR only, because for GB the exact explainer would take hours per window.

## Datasets {#sec:datasets}

Each of the four datasets contains drift with a documented cause, so the verdicts can be checked against known events. Table @tab:datasets summarizes them. The two census tasks come from the American Community Survey (ACS) and use data from California (CA), Texas (TX), New York (NY), Florida (FL) and Washington (WA).

Table: Datasets, drift windows and reference accuracy. Rows gives the smallest and largest window, Inputs the number of features or embedding dimensions and the last two columns the reference test accuracy of LR and GB {#tab:datasets span=2}
<<gen:tab_datasets>>

*ACS Income and ACS Employment.* Both tasks come from the ACS of the United States Census Bureau, as packaged by Folktables [@ding2021retiring]. ACS Income predicts whether a person earns more than \$50,000 from \res{inc-nfeatures} features. ACS Employment predicts, from \res{emp-nfeatures} features, whether a person aged 16 to 90 is employed. With CA 2014 as the reference, the temporal windows are CA 2015 to 2019 and 2021 to 2023, as there is no standard 2020 release [@census2021experimental]. The geographic windows are TX, NY, FL and WA in 2014. In 2019 the relationship variable RELP was replaced by RELSHIPP [@census2019pums], which we map back to RELP using the code labels of the 2018 and 2019 data dictionaries (Table @s:tab:relp in the Supplement). Five documented changes fall within these years: new occupation codes in 2018 [@census2020occupation], a redesigned relationship question in 2019, a new coding of race answers from 2020 [@census2021race], the pandemic and wage growth against the fixed income threshold.

*Gas sensor array drift.* This dataset from the University of California, Irvine (UCI) machine learning repository holds 13,910 measurements of six gases by 16 metal oxide sensors over 36 months, in ten batches [@vergara2012gas; @rodriguezlujan2014gas]. Each measurement has eight features per sensor. As the sensors age, their response to the same gas drifts while the labels stay exact, a documented change in $P(X\mid Y)$. Batches 1 and 2 form the reference and batches 3 to 10 the windows. Because some batches are small, the number of audit labels for a window of $n$ rows is given by $\min(600,\lfloor n/2\rfloor)$.

*CLEAR-10.* This image stream holds ten object classes and a background class in ten time-ordered buckets of about 3,300 images each [@lin2021clear]. Bucket 1 serves as the reference.

## Injection benchmark {#sec:benchmark-setup}

Real drift has no known type, so the diagnosis is graded on injected drift. The benchmark uses the 2014 data of \res{bench-nstates} states (\res{bench-states}) for both ACS tasks. Each state is a reference distribution with its own model, split as above. For each of \res{bench-nseeds} seeds the split, the window and the injection are redrawn, which gives \res{bench-nreps} replicates per configuration. Each replicate draws a production window of \res{bench-prodsize} rows and a grading holdout of \res{bench-holdsize} rows from the test part. Each mechanism is injected into both at three intensities. The audit uses \res{bench-audit-n} labels. Proportions carry Wilson intervals [@wilson1927] and means carry bootstrap intervals over replicates.

*Design A* injects the four types in ways that partly match the tests. Covariate shift rescales two numeric features (ACS Income: \res{bench-cov-features-inc}) for a random subset of rows. Prior shift drops rows of one class until the positive rate rises by \res{bench-prior-steps}. Concept drift inverts the labels of the \res{bench-concept-steps}% of rows with the highest value of one feature (ACS Income: \res{bench-concept-feature-inc}). Label noise flips a random \res{bench-noise-steps}% of labels. Each replicate also includes a control window without drift.

*Design B* uses mechanisms that the tests were not designed for. Covariate shift is selection bias: each row is kept with a probability given by $\sigma(\beta s(x))$, where $\sigma$ is the logistic function, $s$ is a seeded random score over all inputs and $\beta\in\{\res{bench-b-betas}\}$. The rows stay real and $P(Y\mid X)$ is exactly unchanged. Prior shift lowers the positive rate by \res{bench-b-prior-steps}. Concept drift inverts the labels in the top \res{bench-b-concept-steps}% of a second random score, which defines an oblique region that no single feature describes. For ACS Income a second concept drift raises the income threshold to \res{bench-b-thresholds}. Label noise is class-conditional, with positive labels flipped to negative at rates of \res{bench-b-noise-steps}%.

## Baselines and ablations {#sec:baselines}

A diagnosis is only worth its cost if it beats simpler options. Every method names one of the five outcomes (no drift or one of the four types) from the same tests and audit labels. Three rules represent current practice. *Input monitoring* reads any input alarm as covariate shift, which is how drift alarms are commonly read. *BBSE first* reads a shift in the predicted labels as prior shift [@lipton2018bbse; @rabanser2019failing] and any other alarm as covariate shift, which makes it our label-free stage without the consistency test. *Error-rate monitoring* also reads a significant audit accuracy drop as concept drift, like an error-rate detector [@gama2004ddm].

The *learned meta-classifier* tests whether a learned rule could replace the tests. It is a GB model on nine statistics of each window: the evidence $-\log_{10}p$ of each block test, the share of features with residual shift, the BBSE prior change, the CBPE change, the evidence and size of the audit accuracy drop and the evidence of the error structure test. In design A it is validated by leaving one state out. In design B it is trained on design A without the predicted state, so it never sees a held-out mechanism. Three ablations remove the MMD block, remove the confidence term from the audit null or replace the confidence bins by cells of predicted class and confidence.

Our procedure is compared with each other method by the per-replicate difference in the share of correctly typed windows, tested by sign-flip permutation (\res{bench-nflips} flips) with Holm correction. Replicates are the unit of analysis because the windows of one replicate share a model and a reference.

# Results {#sec:results}

The benchmark results come first: how often the type is named, whether the procedure transfers to held-out drift and how well its building blocks work. Real drift follows.

## Drift type against baselines {#sec:res-methods}

The central question is how often each method names the injected type. Table @tab:methods gives the answer for every configuration, each with \res{bench-nreps} replicates.

Table: Share of benchmark windows with the correct drift type (%), for each model family, task and design {#tab:methods}
<<gen:tab_methods stack_models>>

Inc. and Emp. denote ACS Income and ACS Employment. A and B are the two designs. An arrow marks a method that differs significantly from ours after Holm correction: a down arrow means that ours is better and an up arrow that ours is worse. Within each model family the upper block contains the competing methods and the lower block the ablations of our procedure.

With LR on ACS Income, our procedure names the type in \res{b-inc-a-lr-ours-acc}% of design A windows (95% interval \res{b-inc-a-lr-ours-ci}), compared with at most \res{b-inc-a-lr-errorratemonitoring-acc}% for a rule baseline. Each rule can name only some of the five outcomes, which caps its score. Across all eight configurations our procedure is significantly better in \res{bench-nbetter} of the \res{bench-ntests} comparisons with a baseline or the learned rule and significantly worse in \res{bench-nworse}, \res{bench-worse-cells}.

The learned meta-classifier is the strongest competitor on design A. Validated on states it has not seen, it reaches \res{b-inc-a-lr-metaclassifier-acc}% on ACS Income, above our \res{b-inc-a-lr-ours-acc}%. On the held-out mechanisms of design B, however, the picture reverses. Trained on design A, the meta-classifier falls to \res{b-inc-b-lr-metaclassifier-acc}% on ACS Income and \res{b-emp-b-lr-metaclassifier-acc}% on ACS Employment, while our procedure retains \res{b-inc-b-lr-ours-acc}% and \res{b-emp-b-lr-ours-acc}%. The learned rule had tied each type to the size and shape of the injected shift. For example, it associated covariate shift with a large shift in two features and therefore misses selection bias, which moves many features slightly. This is the main argument for tests over a learned rule: the tests encode the definitions of the drift types rather than the appearance of the training examples.

The overall rates hide which types are confused with which, so Fig. @fig:confusion shows this breakdown for LR.

![Injected (rows) and diagnosed (columns) drift types on the benchmark with LR, in counts of windows; darker cells hold a larger share of their row](Fig03.png){#fig:confusion width=83.5}

A perfect result would fill only the diagonal. Because design B has no control windows, false alarms are measured on design A. In design A most errors fall in the label noise row, where noise is read as concept drift or as no drift. The control row holds the false alarms. Our procedure raised them on \res{diag-fa-n} of \res{det-ncontrols} control windows (\res{diag-fa-pct}%), \res{diag-fa-labelfree-n} in the label-free stage and \res{diag-fa-audit-n} in the audit, which is below the bound of \res{diag-fa-bound-pct}% derived in Section @sec:diagnosis. In design B the errors concentrate in the concept and noise rows, for reasons explained in Section @sec:res-mechanisms.

The ablations show which parts of the procedure matter. Removing the confidence term from the audit null costs \res{b-inc-a-lr-noconfidencenull-diffabs} points on ACS Income design A, because uniform label noise then looks like concept drift. Removing the MMD block makes little difference on the benchmark (\res{b-inc-a-lr-nommd-diff} points), whose shifts are visible feature by feature, but its value becomes clear on the image embeddings in Section @sec:res-real. Replacing the confidence bins by cells of predicted class and confidence helps on ACS Employment design B (\res{b-emp-b-lr-classconfidencenull-acc}% against \res{b-emp-b-lr-ours-acc}%) but costs accuracy on ACS Income design A (\res{b-inc-a-lr-classconfidencenull-acc}%). Adopting it now would mean choosing the method after seeing design B, so it remains an ablation and a direction for future work.

## Held-out mechanisms {#sec:res-mechanisms}

Design B asks whether the procedure transfers to drift it was not designed for. It is the stronger of the two tests, since no part of the procedure was shaped by these mechanisms. Table @tab:mechanisms breaks the results down by mechanism.

Table: Design B results by drift mechanism {#tab:mechanisms}
<<gen:tab_mechanisms>>

Corr. is the share of windows typed correctly (%) and Drop is the mean true accuracy drop in points, where a negative value means that accuracy rose. The income threshold mechanism exists only for ACS Income.

Three of the mechanisms transfer well. Selection bias is identified as covariate shift in \res{b-inc-lr-mech-selection-id}% of ACS Income windows with LR, even though no value is distorted and the shift spreads over all features. A lower positive rate is identified as prior shift in \res{b-inc-lr-mech-priordecrease-id}%. Concept drift in an oblique region is found in \res{b-inc-lr-mech-conceptoblique-id}%, although no single feature defines that region.

Two mechanisms do not transfer. Raising the income threshold relabels some rows in every window but barely changes accuracy (mean drop \res{b-inc-lr-mech-conceptthreshold-drop} points). Because the audit first asks whether accuracy fell, it reports no drift in \res{b-inc-lr-mech-conceptthreshold-as-none} of the \res{b-inc-lr-mech-conceptthreshold-n} windows. The procedure is designed to find drift that harms the model, which this drift does not. Class-conditional label noise is identified correctly in only \res{b-inc-lr-mech-classnoise-id}% of ACS Income windows. At low rates the accuracy drop is too small to detect with \res{bench-audit-n} labels. At high rates the errors follow the true class, which correlates with the features, so the error structure test reads the pattern as concept drift. This is a genuine limitation of a null model that conditions on confidence alone. Both failures lie in the audit rather than in the label-free stage.

The same patterns hold for ACS Employment and for GB. On design A our procedure reaches \res{b-emp-a-lr-ours-acc}% on ACS Employment with LR and, with GB, \res{b-inc-a-hgb-ours-acc}% on ACS Income and \res{b-emp-a-hgb-ours-acc}% on ACS Employment. Label noise is the hardest type on ACS Employment, identified in \res{b-emp-a-lr-id-labelnoise}% of windows. The methods rank the same for both model families. The tests read only the model's outputs and its errors, so they need no modification for a nonlinear model.

## Detection and accuracy estimation {#sec:res-detection}

The diagnosis builds on the detectors and the accuracy estimate, so both are also checked on the benchmark. Table @tab:detectors gives the alarm rate of each detector by injected type, pooled over the four design A configurations.

Table: Detector alarm rates on design A by injected type {#tab:detectors}
<<gen:tab_detectors>>

The no drift column is the false alarm rate with its 95% confidence interval (CI). Over \res{det-ncontrols} control windows every interval contains $\alpha=\res{acs-alpha}$ or lies below it. Every detector catches covariate shift and all except PSI also catch most prior shifts. Concept drift and label noise windows share their inputs with the control window of their replicate, so no detector can see them, which is why the audit is needed. Table @tab:estimators compares the four accuracy estimates by their mean absolute error against the measured accuracy.

Table: Mean absolute error of the label-free accuracy estimates (points) {#tab:estimators}
<<gen:tab_estimators estimators_short>>

Cov. and Conc. denote covariate shift and concept drift, Inc. and Emp. the two ACS tasks. The smallest error in each column is shown in bold. On design A the errors of all four estimates stay below \res{est-bench-none-max} points without drift and below \res{est-bench-covariate-max} under covariate shift. Under concept drift and label noise every error equals the whole loss, about \res{est-bench-conceptnoise-cbpe} points, because the inputs do not change. Across these \res{est-ncols} comparisons, ATC has the smallest error in \res{est-nbest-atc} and CBPE in only \res{est-nbest-cbpe}. On the gas sensor data all four are off by \res{est-gas-best} to \res{est-gas-worst} points on average. In batch 8 the LR model's mean confidence falls from \res{gas-ref-conf} to \res{gas-b8-conf} and its accuracy to \res{gas-b8-acc}, yet CBPE estimates \res{gas-b8-est}, so the estimate is best read as an upper bound on accuracy.

## Real drift {#sec:res-real}

Real drift has no known type, but its causes are documented. The question here is whether the verdicts agree with those causes and whether the control windows stay quiet. Fig. @fig:timelines shows how accuracy evolves over time in all four datasets.

![Measured accuracy of both models and the label-free CBPE estimate on the temporal windows](Fig04.png){#fig:timelines width=83.5}

C marks the control window and the numbers mark years (ACS), batches (gas sensor) or buckets (CLEAR-10). The gap in the ACS lines marks the missing 2020 release.

ACS Income shows the clearest trend, so we discuss it first. Its accuracy falls over time for both models, from \res{inc-ca2015-acc} in 2015 to \res{inc-ca2023-acc} in 2023 with LR, while the CBPE estimate falls much less. Table @tab:income gives the details behind the ACS Income panel of Fig. @fig:timelines.

Table: Detection and diagnosis on the ACS Income windows. The alarms are those of the LR model: K is the KS test, M the MMD test, C the confidence test, B BBSD and D the domain classifier {#tab:income}
<<gen:tab_income income_narrow>>

Δ is the accuracy change in points and Est. err. the error of the CBPE estimate. A tick marks an alarm. Type is the verdict of the diagnosis, which is the same for LR and GB in every window (Cov. denotes covariate shift). Top shifts lists the two features with the largest effect size: occupation (OCCP), place of birth (POBP), relationship (RELP) and race (RAC1P).

The control window raises no alarm with either model. CA 2015, whose accuracy did not change significantly, is diagnosed as no drift by both models, while every other window is diagnosed as covariate shift. The documented events appear in the localization. When the occupation codes were revised in 2018, \res{inc-ca2018-unseen-occp}% of rows carried a code never seen in 2014. The model's reliance on occupation then fell (SHAP change \res{inc-ca2018-shap-occp}). After the relationship question was redesigned in 2019, relationship shifts with an effect size of \res{inc-ca2019-eff-relp}. From 2021 onward race shifts with an effect size of \res{inc-ca2021-eff-rac1p}, following the change in how the Census Bureau codes written race answers [@census2021race]. Wage growth against the fixed threshold shows up in the labels. The share of positive labels rises from \res{inc-ctrl-posrate} in the control window to \res{inc-ca2023-posrate} in 2023, while the model predicts only \res{inc-ca2023-predposrate}. Part of the 2023 loss is therefore a change in the labeling rule, which no label-free test can see.

The other datasets differ in how much the drift costs. On ACS Employment every window is diagnosed as covariate shift, yet accuracy changes by at most \res{emp-dacc-maxabs} points with LR. The inputs do move, including relationship in 2019 and race from 2021, but the model is barely affected. A drift alarm alone would overstate the problem here, whereas the accuracy estimate and the audit put it in proportion. Every gas sensor batch is also diagnosed as covariate shift. With LR, accuracy changes by \res{gas-b8-dacc} points in batch 8. This matches the known cause: aging sensors change $P(X\mid Y)$. BBSE first labels every one of these batches as a prior shift because the predicted labels move as well, but the consistency test shows that they move because the sensors read differently, not because the mix of gases changed.

On CLEAR-10 the change is subtle. Both models report no drift in buckets \res{clr-windownums-none} and covariate shift in buckets \res{clr-windownums-covariate}. In buckets \res{clr-windownums-mmdonly} no single embedding dimension shifts significantly with LR. Only the MMD test detects the change, while the predicted labels stay put. These buckets show why the multivariate block is needed. The only detector alarm on a control window comes from the domain classifier baseline on CLEAR-10 ($p=\res{clr-ctrl-dc-p}$), a false alarm of the kind that $\alpha$ allows.

## Reliability and triage {#sec:res-reliability}

The last two stages score individual predictions and advise on retraining. The fused risk score is judged by how well it ranks wrong predictions. Where the fusion is learned, on ACS and CLEAR-10, its area under the receiver operating characteristic curve (AUROC) differs from that of confidence alone by \res{rel-other-diff-min} to \res{rel-other-diff-max} over \res{rel-other-n} windows and by \res{rel-bench-gain-min} to \res{rel-bench-gain-max} on the benchmark. On the gas sensor array the calibration part contains too few wrong predictions (\res{rel-gas-lr-cal-errors} with LR and \res{rel-gas-hgb-cal-errors} with GB), so the risk falls back to confidence. Confidence alone already carries most of the information about a single prediction.

A retrain truly helps when retraining with importance weights or on the latest labeled window significantly raises holdout accuracy. Over \res{rem-n} real settings (Table @s:tab:remediation in the Supplement), the triage is right in \res{rem-recent-correct} of the \res{rem-recent-n} settings that have an earlier labeled window, because its recent-window probe is validated on real labels. Without one it relies on importance-weighted validation and is right in \res{rem-norecent-correct} of \res{rem-norecent-n} settings, but mostly by advising against retraining, since one truly helped in only \res{rem-norecent-helps} of them. On the benchmark its recall is \res{b-inc-a-lr-triage-recall}%, because importance-weighted validation cannot see gains outside the reference data.

# Discussion {#sec:discussion}

The results support the central claim. A diagnosis built from tests of the type definitions transfers to drift it was not designed for, whereas a learned rule does not. The cost is a small label audit, needed only for concept drift and label noise.

Several limitations qualify these findings. Each benchmark window contains a single type, while real windows such as ACS Income 2023 mix several. The four types are also an idealization: sensor aging changes $P(X\mid Y)$ and, through it, $P(Y\mid X)$, yet our procedure reports it as covariate shift. Design B reduces, but cannot eliminate, the risk that the benchmark favors the tests. The weighted residual tests also ignore the sampling error of the BBSE weights. With hundreds of thousands of rows even small shifts become significant, which is why effect sizes are reported next to every decision. Deep models trained end to end, text and streaming data are not covered.

# Conclusions {#sec:conclusion}

We showed that the drift type, which determines the response, can be identified by hypothesis tests with a stated error rate from label-free tests and a few hundred late labels. On injected drift the procedure outperforms rules from monitoring practice and the label shift literature, works for both model families and, unlike a learned meta-classifier, transfers to held-out drift. On real drift it reported no drift on any control window and traced documented events, from new occupation codes to aging sensors.

Drift that leaves accuracy intact passes the audit unnoticed, while class-conditional label noise is often read as concept drift. Future work will condition the audit on the full model output, model the sampling error of the BBSE weights and test mixed drift.

# References {-}
