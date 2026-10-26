---
title: Drift Detection and Diagnosis for Deployed Machine Learning Models
author: Rahul Guhagarkar
author: Nathan Cherian
author: Alok Pal
author: Akul Patre
author: Sanjay Mirchandani
affiliation: Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: 2023.rahul.guhagarkar@ves.ac.in
keywords: Concept Drift, Label Shift, Model Monitoring, Drift Diagnosis, Hypothesis Testing
---

% DSISys 2026 version: the DACS text (paper/dacs/paper.md) on the Springer LNCS Word
% template, exactly 12 pages, anonymous for double-blind review. Build with
% examples/paper/build_springer12.py dsisys.

::: abstract
Deployed machine learning models lose accuracy when production data drift away from the training data. Monitoring tools raise an alarm when this happens but seldom say what kind of drift occurred, although the right response depends on it: covariate shift calls for reweighting, prior shift for recalibration, concept drift for fresh labels and label noise for a check of the labeling process. This paper presents Data Drift Autopsy, an end-to-end monitoring pipeline that detects drift, estimates the lost accuracy without labels, locates the shifted features, names the drift type, scores the trust due to each prediction and advises whether a cheap retrain will help. At its heart sits a diagnosis made only of hypothesis tests, all held to one family-wise error rate. Its first stage uses no labels and tells covariate shift from prior shift. The second stage is new: given a few hundred late labels, it asks whether the errors have moved in a way the model's own confidence cannot account for, the mark that sets concept drift apart from label noise. With drift injected into two census tasks and two model families, the diagnosis named the type in \res{bench-a-ours-min} to \res{bench-a-ours-max}% of windows, ahead of common monitoring rules. A learned meta-classifier did better on drift it had seen, yet fell to \res{bench-b-meta-min} to \res{bench-b-meta-max}% on held-out drift mechanisms, where our tests still reached \res{bench-b-ours-min} to \res{bench-b-ours-max}%. On four real datasets with documented changes, the pipeline flagged no control window and pointed to the known events.
:::

# Introduction {#sec:intro}

Nobody announces it when a deployed classifier starts to slip. The production data simply wander away from the training data, while the labels that would expose the loss tend to turn up weeks or months later [@rabanser2019failing]. A monitor has to catch the change and make sense of it before those labels exist.

Existing monitors do the first part of that job well. They flag a changed distribution [@rabanser2019failing] and give a fair estimate of how much accuracy has gone [@kivimaki2025performance]. Far fewer say what kind of change took place. That gap matters, since each kind has its own remedy. Moreno-Torres et al. [@moreno2012unifying] distinguish three types of dataset shift. Under covariate shift the inputs drift but the mapping from inputs to labels holds, so reweighting the training data is often enough. Under prior shift it is only the class balance that moves, which recalibration usually fixes. Concept drift alters the mapping itself; nothing short of fresh labels will repair it. To these we add label noise as a fourth type. Here the labels used to grade the model are themselves corrupted, so the fault lies in how labels are collected rather than in the model.

This paper presents Data Drift Autopsy, an end-to-end monitoring pipeline that takes a deployed model, its labeled training data and a stream of unlabeled production data. For every production window it answers the questions a monitoring team asks in turn. Has the data changed? How much accuracy has been lost? Which features moved? What type of drift is it and what probably caused it?

The core of the pipeline is the step that names the drift type, which is also the main subject of this paper. Nothing in this step is learned from examples of drift: it is a handful of hypothesis tests that share one significance level and one family-wise error rate. The first stage, which needs no labels, combines existing tools. The second stage is new. It uses a few hundred late labels to ask whether accuracy has dropped and, if so, whether the errors changed in a way that depends on some input feature. Uniform label noise changes the error rate only in line with how confident the model is, while concept drift changes it inside one region of the input space. Because every step is a formal test, the false alarm rate is fixed before the data are seen.

We evaluate the diagnosis on a benchmark of injected drift where the true type is known. We also run the whole pipeline on four real datasets whose changes are documented. The benchmark includes drift mechanisms that the tests were not designed for, so that a method tuned to its own benchmark cannot look good by construction. The contributions are as follows.

1. An audit test that separates concept drift from label noise using only a few hundred late labels. Existing shift tests, such as DetectShift [@maiapolo2023detectshift], either need labeled production data or do not consider label noise.
2. A hierarchical procedure that combines this audit with a label-free stage and names four drift types under family-wise error control.
3. A benchmark covering two tabular tasks and two model families, with matched as well as held-out drift mechanisms. It shows that tests built on the definitions of the types carry over to new drift, while a learned rule does not.
4. An end-to-end monitoring pipeline that covers detection, accuracy estimation, localization and diagnosis, evaluated on four real drifts with documented causes.

# Related work {#sec:sota}

*Drift types.* DetectShift tests for a change in the joint distribution of inputs and labels and in each of its parts, $P(X)$, $P(Y)$, $P(X\mid Y)$ and $P(Y\mid X)$ [@maiapolo2023detectshift]. It needs labels for the new data, however, which its authors acknowledge as a limitation. We keep the same definitions, add label noise as a fourth type and ask for labels only in a small audit.

*Label shift.* Black-box shift estimation (BBSE) recovers the new class prior from the confusion matrix of any classifier [@lipton2018bbse]. It assumes that the inputs inside each class stay as they were, which is exactly the property that separates prior shift from covariate shift. Roschewitz et al. [@roschewitz2025shiftid] test this property on medical images. They resample the reference data to the estimated prevalence and attribute the shift to prevalence if the features then stop differing. Our label-free stage follows the same idea. It differs in two ways: it uses importance weights in place of resampling and it puts every label-free decision into one family with a stated error rate.

In short, each prior method solves part of the problem. To our knowledge, no published method separates concept drift from label noise with a small label audit. Neither has any type diagnosis been tested on drift mechanisms held out from its design.

# Method {#sec:method}

This section first defines the four drift types precisely and then follows the data through the pipeline introduced in Section @sec:intro. Fig. @fig:architecture lays out the stages.

![Stages of the monitoring pipeline, from the inputs (A) to the advice on retraining (F). SHAP stands for Shapley additive explanations, CAM for class activation maps and OOD for out-of-distribution](Fig01.png){#fig:architecture width=100}

Stages A to C bring the data into a common form, test whether anything has changed and estimate how much accuracy the change may cost. Stage D, the core of the paper, names the type of change and points to its likely cause. Stages E and F act on what was found, first for single predictions and then for the decision to retrain; this paper does not evaluate them. Every decision in the pipeline is a hypothesis test at the significance level $\alpha=\res{acs-alpha}$. When many tests are run together, the chance of at least one false alarm is held at $\alpha$ by the Holm procedure [@holm1979], its weighted form or its Bonferroni bound.

## Notation and drift types {#sec:types}

To test for a drift type we first have to say exactly what that type changes. Write $P(X,Y)$ for the distribution of inputs $X$ and labels $Y$ behind the reference data. A production window (a batch of rows from a later period or from another region) is drawn from $Q(X,Y)$. On every row the model outputs a predicted label $\hat y$ together with a confidence $c$, taken as its largest class probability. The four types differ in what changes between $P$ and $Q$. Covariate shift has $Q(X)\neq P(X)$ while $Q(Y\mid X)=P(Y\mid X)$. Prior shift has $Q(Y)\neq P(Y)$ while $Q(X\mid Y)=P(X\mid Y)$. Concept drift has $Q(Y\mid X)\neq P(Y\mid X)$. Label noise is different again: the true distribution does not move at all, yet each label we observe may have been flipped with some probability. An audit means a random sample of $m$ production rows whose labels come in late. A control window is drawn from the reference distribution itself, so no alarm should fire on it.

## Reference split, detection and estimation {#sec:detection}

Stage C answers three questions: have the data moved, how much accuracy might the change cost and where in the inputs is it located? The labeled reference data are split into three disjoint parts, stratified by class: \res{acs-split-pct-train}% for training, \res{acs-split-pct-calibration}% for calibration and \res{acs-split-pct-test}% for testing. The calibration part is the reference window for every detector and fits the accuracy estimator. The test part gives the reference accuracy and doubles as the control window. Images are mapped to the \res{clear-dim}-dimensional output of the global average pooling layer of a frozen residual network with 18 layers (ResNet-18) trained on ImageNet [@he2016deep].

Three detectors decide whether the inputs or the model outputs have moved. The Kolmogorov–Smirnov (KS) test compares each numeric feature, with a Bonferroni correction over features. The maximum mean discrepancy (MMD) test [@gretton2012kernel] compares all standardized inputs jointly through a Gaussian kernel, with a permutation p value. The confidence test compares histograms of $c$ with a $\chi^2$ test of homogeneity.

Labels arrive late, so the accuracy is first estimated from the model's own confidence with confidence-based performance estimation (CBPE) [@kivimaki2025performance]. A map $a(\cdot)$ from confidence to the probability of a correct prediction is fitted by histogram binning on the calibration part. For a window with confidences $c_1$ to $c_n$, the estimate $\hat A$ is given by

$$\hat A = \frac{1}{n}\sum_{i=1}^{n} a(c_i)$$. {#eq:cbpe}

An alarm helps more when it also says where the change sits. Localization tests every feature, with KS for numeric features and the $\chi^2$ homogeneity test for nominal ones, under Holm correction. It reports an effect size between 0 and 1 for each feature: the KS statistic or Cramér's $V$. For nominal features it also gives the share of production rows whose category never occurs in the reference.

## Drift type diagnosis {#sec:diagnosis}

Stage D turns an alarm into one of the four types and thereby into a response. It follows the decision path in Fig. @fig:decision. The questions in the upper row use no labels and separate covariate shift from prior shift. The lower row separates concept drift from label noise. It runs only when no label-free test rejects and an audit is available.

![Decision path that names the drift type. Questions are shown in white boxes and verdicts in gray boxes; the upper row needs no labels and the lower row uses the audit](Fig02.png){#fig:decision width=83.5}

*Label-free stage.* The first question is whether anything has moved at all. Three blocks of tests answer it: the feature tests, a $\chi^2$ test on the predicted labels and the MMD test. They form one family tested at level $\alpha$ with a weighted Holm procedure [@holm1979]. A test that rejects hands its weight on to those still waiting, which is how the family-wise error rate survives every label-free decision.

A rejection raises the next question: could a change in the class balance alone produce what we see? To find out, BBSE first estimates the new class prior. Let $C_{jk}=P(\hat y=j,y=k)$ on the calibration part and let $\mu_j$ be the share of production predictions that fall in class $j$. The class weights $w_k=Q(Y=k)/P(Y=k)$ are given by the solution of

$$C\,w = \mu$$. {#eq:bbse}

\noindent If the shift really is a pure prior shift, each class keeps its own input distribution. Reweighting every reference row by the weight $w_{y}$ of its class, as given by Eq. (@eq:bbse), ought then to reproduce the production inputs. Checking this is the label shift consistency test, which borrows the prevalence adjustment idea of Roschewitz et al. [@roschewitz2025shiftid]. The feature tests are repeated against the weighted reference. A feature that still differs carries a covariate shift. If no feature differs and the predicted labels have moved, the shift is a prior shift.

*Audit stage.* Concept drift and label noise do not touch the inputs or the model outputs, so only labels can reveal them. The audit draws $m$ late labels and first checks, with a one-sided two-proportion test, whether accuracy has dropped. If it has, the next question is whether the change in errors depends on a feature. To answer it, a logistic model of whether a prediction is correct is fitted on the calibration rows and the audit rows together. Its null form holds \res{const-quantile-bins} confidence bins at reference quantiles, bins of a feature $f$, an audit indicator and the interaction of that indicator with the confidence bins. The alternative adds the interaction of the indicator with the bins of $f$. A likelihood ratio test compares the two for each feature.

The confidence term is what separates the two types. In a binary task, uniform label noise at rate $r$ makes the probability of a correct prediction equal to $r+(1-2r)\,q(x)$, where $q(x)$ is the model's own probability of being right at $x$. The change therefore depends on $x$ only through $q(x)$, which the confidence bins of the null absorb. Concept drift, by contrast, moves the errors inside a region of some feature. A feature that stays significant after Holm correction therefore points to concept drift. If no feature is significant, the verdict is label noise. Each of the two stages is tested at level $\alpha$, so a window without drift receives a drift verdict with probability at most $2\alpha$.

# Experimental setup {#sec:setup}

The experiments are built around two questions. First, does the procedure name the type correctly when the truth is known, including for drift it was not designed for? Second, does it behave sensibly on real drift, where the type is unknown but the causes are on record?

*Protocol.* Every setting below was fixed before the evaluation that uses it. The diagnosis was frozen before the held-out design B was run for the first time.

## Models

A diagnosis that worked for only one kind of model would be of limited use, so the pipeline monitors two untuned model families. The first is logistic regression (LR) with $L_2$ regularization ($C=1$) on standardized numeric and one-hot encoded nominal features. The second is histogram gradient boosting (GB) from scikit-learn [@pedregosa2011scikit] with default settings, no early stopping and native splits on nominal codes. For CLEAR-10 both models work on the frozen embeddings.

## Datasets {#sec:datasets}

The real datasets were chosen because the cause of their drift is documented, which lets us check the verdicts against known events. Two are census tasks from the American Community Survey (ACS) with data from California (CA), Texas (TX), New York (NY), Florida (FL) and Washington (WA). The other two are a gas sensor array and an image stream.

*ACS Income and ACS Employment.* Both tasks come from the ACS of the United States Census Bureau, as packaged by Folktables [@ding2021retiring]. ACS Income predicts from \res{inc-nfeatures} features whether a person earns more than \$50,000. ACS Employment predicts from \res{emp-nfeatures} features whether a person aged 16 to 90 is employed. CA 2014 is the reference. The temporal windows are CA 2015 to 2019 and 2021 to 2023, as no standard 2020 release exists [@census2021experimental]. Five documented changes fall in these years: new occupation codes in 2018 [@census2020occupation], a redesigned relationship question in 2019, a new coding of race answers from 2020 [@census2021race], the pandemic and wage growth against the fixed income threshold.

*Gas sensor array drift.* This dataset from the machine learning repository of the University of California, Irvine (UCI) holds 13,910 measurements of six gases by 16 metal oxide sensors, taken over 36 months in ten batches [@vergara2012gas]. As the sensors age, their response to the same gas drifts while the labels stay exact. This is a documented change in $P(X\mid Y)$. Batches 1 and 2 form the reference and batches 3 to 10 the windows.

*CLEAR-10.* This image stream has ten object classes and a background class, spread over ten time-ordered buckets of about 3,300 images each [@lin2021clear]. Bucket 1 is the reference.

## Injection benchmark {#sec:benchmark-setup}

The type of a real drift is never known for certain, so the diagnosis is graded on drift that we inject ourselves. The benchmark uses the 2014 data of \res{bench-nstates} states (\res{bench-states}) for both ACS tasks. For each of \res{bench-nseeds} seeds the split, the window and the injection are drawn again, which gives \res{bench-nreps} replicates per configuration. A replicate draws a production window of \res{bench-prodsize} rows and a grading holdout of \res{bench-holdsize} rows from the test part. Each mechanism is injected into both at three intensities. The audit uses \res{bench-audit-n} labels.

*Design A* injects the four types in ways that partly match how the tests work. Covariate shift rescales two numeric features (ACS Income: \res{bench-cov-features-inc}) for a random subset of rows. Prior shift drops rows of one class until the positive rate rises by \res{bench-prior-steps}. Concept drift inverts the labels of the \res{bench-concept-steps}% of rows with the highest value of one feature (ACS Income: \res{bench-concept-feature-inc}). Label noise flips a random \res{bench-noise-steps}% of the labels. Each replicate also contains a control window without drift.

*Design B* uses mechanisms that the tests were not built for. Covariate shift becomes selection bias. Each row is kept with a probability given by $\sigma(\beta s(x))$, where $\sigma$ is the logistic function, $s$ is a seeded random score over all inputs and $\beta\in\{\res{bench-b-betas}\}$. The rows stay real and $P(Y\mid X)$ is exactly unchanged. Prior shift lowers the positive rate by \res{bench-b-prior-steps}. Concept drift inverts the labels in the top \res{bench-b-concept-steps}% of a second random score, which marks out an oblique region that no single feature describes. For ACS Income a second concept drift raises the income threshold to \res{bench-b-thresholds}. Label noise is class-conditional: positive labels are flipped to negative at rates of \res{bench-b-noise-steps}%.

## Baselines {#sec:baselines}

A diagnosis is only worth running if it does better than simpler options. Every method below names one of the five outcomes (no drift or one of the four types) from the same tests and the same audit labels. Three rules stand for current practice. *Input monitoring* reads any input alarm as covariate shift, which is how drift alarms are commonly read. *BBSE first* reads a shift in the predicted labels as prior shift [@lipton2018bbse; @rabanser2019failing] and any other alarm as covariate shift. It is our label-free stage without the consistency test. *Error-rate monitoring* also reads a significant drop in audit accuracy as concept drift, as an error-rate detector would [@gama2004ddm].

The *learned meta-classifier* checks whether a learned rule could replace the tests. It is a GB model trained on nine statistics of each window. In design A it is validated by leaving one state out. In design B it is trained on design A without the state being predicted, so it never sees a held-out mechanism.

Each method is compared with ours through the per-replicate difference in the share of correctly typed windows, tested by sign-flip permutation (\res{bench-nflips} flips) with Holm correction.

# Results {#sec:results}

The benchmark comes first: how often the type is named and whether the procedure carries over to drift it was not designed for. Real drift follows.

## Drift type against baselines {#sec:res-methods}

The most direct test of the diagnosis is how often it names the injected type, compared with the baselines. Table @tab:methods gives this share for every configuration, each with \res{bench-nreps} replicates.

Table: Share of benchmark windows with the correct drift type (%), for each model family, task and design {#tab:methods}
<<gen:tab_methods stack_models_main>>

Inc. and Emp. stand for ACS Income and ACS Employment. A and B are the two designs. An arrow marks a method that differs significantly from ours after Holm correction: a down arrow means that ours is better and an up arrow that ours is worse.

With LR on ACS Income, our procedure names the type in \res{b-inc-a-lr-ours-acc}% of design A windows (95% interval \res{b-inc-a-lr-ours-ci}). The best rule baseline reaches \res{b-inc-a-lr-errorratemonitoring-acc}%. Over all eight configurations our procedure is significantly better in \res{bench-nbetter} of the \res{bench-ntests} comparisons with a baseline or the learned rule. It is significantly worse in \res{bench-nworse}, \res{bench-worse-cells}.

On design A the learned meta-classifier is the strongest competitor. Validated on states it has not seen, it reaches \res{b-inc-a-lr-metaclassifier-acc}% on ACS Income, above our \res{b-inc-a-lr-ours-acc}%. The held-out mechanisms of design B turn this around. Trained on design A, the meta-classifier drops to \res{b-inc-b-lr-metaclassifier-acc}% on ACS Income and \res{b-emp-b-lr-metaclassifier-acc}% on ACS Employment, while our procedure keeps \res{b-inc-b-lr-ours-acc}% and \res{b-emp-b-lr-ours-acc}%. The learned rule had tied each type to the size and shape of the injected shift. It had learned, for example, that covariate shift means a large shift in two features. It therefore misses selection bias, which moves many features a little. This is the main argument for tests over a learned rule. The tests encode what the drift types are, not what the training examples happened to look like.

The overall rates do not show which types get confused with which. Fig. @fig:confusion breaks the results down by type for LR.

![Injected (rows) and diagnosed (columns) drift types on the benchmark with LR, in counts of windows; darker cells hold a larger share of their row](Fig03.png){#fig:confusion width=76}

A perfect diagnosis would fill only the diagonal. Design B has no control windows, so false alarms are measured on design A. There, most errors sit in the label noise row, where noise is read either as concept drift or as no drift. The control row holds the false alarms. Our procedure raised one on \res{diag-fa-n} of \res{det-ncontrols} control windows (\res{diag-fa-pct}%), \res{diag-fa-labelfree-n} in the label-free stage and \res{diag-fa-audit-n} in the audit. That is below the bound of \res{diag-fa-bound-pct}% derived in Section @sec:diagnosis.

## Held-out mechanisms {#sec:res-mechanisms}

Design B asks whether the procedure carries over to drift it was not built for.

Three of the five mechanisms carry over well. Selection bias is named covariate shift in \res{b-inc-lr-mech-selection-id}% of ACS Income windows with LR, even though no value is distorted and the shift is spread across all features. A lower positive rate is named prior shift in \res{b-inc-lr-mech-priordecrease-id}%. Concept drift in an oblique region, which no single feature bounds, is still recognized in \res{b-inc-lr-mech-conceptoblique-id}%.

The other two mechanisms are harder. A higher threshold relabels some rows in each window, yet model accuracy hardly moves (mean drop \res{b-inc-lr-mech-conceptthreshold-drop} points). With almost nothing lost, the audit stops at its first question and reports no drift in \res{b-inc-lr-mech-conceptthreshold-as-none} of the \res{b-inc-lr-mech-conceptthreshold-n} windows. This is intended, as the procedure looks for drift that costs accuracy and this drift costs almost none. Class-conditional label noise is recognized in only \res{b-inc-lr-mech-classnoise-id}% of ACS Income windows, for two reasons. At low flip rates the loss of accuracy is too small to show up in \res{bench-audit-n} labels. At high rates the errors follow the true class, which is itself correlated with the features, so the error structure test reads the pattern as concept drift. A null model built on confidence alone cannot separate the two, a true limitation.

## Real drift {#sec:res-real}

On real data the type of drift is not known, but its causes are on record. Fig. @fig:timelines shows how accuracy changes over time in all four datasets.

![Measured accuracy of both models and the label-free CBPE estimate on the temporal windows](Fig04.png){#fig:timelines width=122}

C marks the control window. The numbers mark years (ACS), batches (gas sensor) or buckets (CLEAR-10). The gap in the ACS lines is the missing 2020 release.

ACS Income shows the clearest trend, so we start there. Its accuracy falls over time for both models, with LR going from \res{inc-ca2015-acc} in 2015 to \res{inc-ca2023-acc} in 2023, while the CBPE estimate of Eq. (@eq:cbpe) falls far less.

Neither model raises an alarm on the control window. Both call CA 2015, whose accuracy did not change significantly, no drift and every other window covariate shift. The documented events can be read off the localization. The 2018 revision of the occupation codes left \res{inc-ca2018-unseen-occp}% of rows with a code that never occurred in 2014. Relationship moves in 2019 (effect size \res{inc-ca2019-eff-relp}), when its survey question was redesigned. Race moves from 2021 (effect size \res{inc-ca2021-eff-rac1p}), once the Census Bureau had changed its coding of written race answers [@census2021race]. Wage growth, measured against a fixed income threshold, shows up in the labels instead: their positive share rises from \res{inc-ctrl-posrate} in the control window to \res{inc-ca2023-posrate} in 2023 while the model predicts only \res{inc-ca2023-predposrate}. Part of the 2023 loss comes from a change in what the labels mean, something no label-free test can detect.

On ACS Employment every window is diagnosed as covariate shift, yet LR accuracy never changes by more than \res{emp-dacc-maxabs} points; relationship (2019) and race (from 2021) shift there as well while the model barely responds. The gas sensor batches all come out as covariate shift too, as they should for aging sensors that alter $P(X\mid Y)$. BBSE at first takes each gas batch for a prior shift, since the predicted labels move too. The consistency test corrects this: the sensors respond differently to a gas mix that has not changed.

CLEAR-10 drifts more gently: buckets \res{clr-windownums-none} show no drift for either model, while buckets \res{clr-windownums-covariate} show covariate shift. In buckets \res{clr-windownums-mmdonly} no single embedding dimension shifts significantly with LR. Only the MMD test sees the change while the predicted labels stay put, which is why the multivariate block is needed.

# Discussion and conclusions {#sec:discussion}

This paper showed that hypothesis tests with a stated error rate can name the drift type, which decides the right response, from label-free tests and a few hundred late labels. On injected drift the procedure beats rules from monitoring practice and the label shift literature and works for both model families. Unlike a learned meta-classifier, it also carries over to held-out drift, because the tests encode the definitions of the types. On real drift it reported no drift on any control window and traced documented events, from new occupation codes to aging sensors.

Several limits apply. Each benchmark window holds a single type, while real windows such as ACS Income 2023 mix several. The four types are also an idealization: sensor aging changes $P(X\mid Y)$ and, through it, $P(Y\mid X)$, yet our procedure reports it as covariate shift. The audit lets through drift that does not hurt accuracy and often mistakes class-conditional label noise for concept drift. Deep models trained end to end, text and streaming data remain untested. The next steps are an audit conditioned on the full model output and benchmark windows that mix several types.

# References {-}
