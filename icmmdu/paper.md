---
title: Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models
author: Rahul Guhagarkar
author: Nathan Cherian
author: Alok Pal
author: Akul Patre
author: Sanjay Mirchandani
affiliation: Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: 2023.rahul.guhagarkar@ves.ac.in
keywords: Concept Drift, Label Shift, Model Monitoring, Drift Diagnosis, Hypothesis Testing
running: Drift Detection, Diagnosis and Reliability Analysis
---

% ICMMDU 2026 version: the PPEECS paper with its supplement merged in. Every number is
% a \res{key} from paper/generated/results.tex; build with examples/paper/build_icmmdu.py.

::: abstract
Deployed machine learning models lose accuracy when production data drift away from the training data. Monitoring tools raise an alarm when this happens but seldom say what kind of drift occurred, although the right response depends on it: covariate shift calls for reweighting, prior shift for recalibration, concept drift for fresh labels and label noise for a check of the labeling process. This paper presents Data Drift Autopsy, an end-to-end monitoring pipeline that detects drift, estimates the lost accuracy without labels, locates the shifted features, names the drift type, scores the trust due to each prediction and advises whether a cheap retrain will help. At its heart sits a diagnosis made only of hypothesis tests, all held to one family-wise error rate. Its first stage uses no labels and tells covariate shift from prior shift. The second stage is new: given a few hundred late labels, it asks whether the errors have moved in a way the model's own confidence cannot account for, the mark that sets concept drift apart from label noise. With drift injected into two census tasks and two model families, the diagnosis named the type in \res{bench-a-ours-min} to \res{bench-a-ours-max}% of windows, ahead of common monitoring rules. A learned meta-classifier did better on drift it had seen, yet fell to \res{bench-b-meta-min} to \res{bench-b-meta-max}% on held-out drift mechanisms, where our tests still reached \res{bench-b-ours-min} to \res{bench-b-ours-max}%. On four real datasets with documented changes, the pipeline flagged no control window and pointed to the known events.
:::

# Introduction {#sec:intro}

Nobody announces it when a deployed classifier starts to slip. The production data simply wander away from the training data, while the labels that would expose the loss tend to turn up weeks or months later [@rabanser2019failing]. A monitor has to catch the change and make sense of it before those labels exist.

Existing monitors do the first part of that job well. They flag a changed distribution [@rabanser2019failing] and give a fair estimate of how much accuracy has gone [@garg2022atc; @kivimaki2025performance]. Far fewer say what kind of change took place. That gap matters, since each kind has its own remedy. Moreno-Torres et al. [@moreno2012unifying] distinguish three types of dataset shift. Under covariate shift the inputs drift but the mapping from inputs to labels holds, so reweighting the training data is often enough. Under prior shift it is only the class balance that moves, which recalibration usually fixes. Concept drift alters the mapping itself; nothing short of fresh labels will repair it. To these we add label noise as a fourth type. Here the labels used to grade the model are themselves corrupted, so the fault lies in how labels are collected rather than in the model.

Telling these types apart is harder than detecting that something changed. Covariate shift and prior shift both move the inputs and the predictions. Concept drift and label noise, on the other hand, leave the inputs as they were, so no test that looks only at unlabeled data can see them.

This paper presents Data Drift Autopsy, an end-to-end monitoring pipeline that takes a deployed model, its labeled training data and a stream of unlabeled production data. For every production window it answers the questions a monitoring team asks in turn. Has the data changed? How much accuracy has been lost? Which features moved? What type of drift is it and what probably caused it? Which individual predictions should not be trusted? Would a cheap retrain recover the loss? The pipeline works for tabular and image models. Every result is written to one report that an interactive dashboard presents (Section @sec:dashboard). Fig. @fig:architecture lays out the stages of the pipeline.

![Stages of the monitoring pipeline, from the inputs (A) to the advice on retraining (F)](Fig01.png){#fig:architecture width=85}

The core of the pipeline is the step that names the drift type, which is also the main subject of this paper. Nothing in this step is learned from examples of drift: it is a handful of hypothesis tests that share one significance level and one family-wise error rate. The first stage, which needs no labels, combines existing tools. After testing the inputs and the predictions for a shift, it estimates the new class balance with black-box shift estimation (BBSE) [@lipton2018bbse] and, borrowing an idea from Roschewitz et al. [@roschewitz2025shiftid], checks whether that balance alone accounts for the change in the inputs. If it does, the shift is a prior shift; if it does not, it is covariate shift. The second stage is new. It uses a few hundred late labels to ask whether accuracy has dropped and, if so, whether the errors changed in a way that depends on some input feature. Uniform label noise changes the error rate only in line with how confident the model is, while concept drift changes it inside one region of the input space. Because every step is a formal test, the false alarm rate is fixed before the data are seen.

We evaluate the diagnosis on a benchmark of injected drift where the true type is known. We also run the whole pipeline on four real datasets whose changes are documented. The benchmark includes drift mechanisms that the tests were not designed for, so that a method tuned to its own benchmark cannot look good by construction. The contributions are as follows.

1. An audit test that separates concept drift from label noise using only a few hundred late labels. Existing shift tests, such as DetectShift [@maiapolo2023detectshift], either need labeled production data or do not consider label noise.
2. A hierarchical procedure that combines this audit with a label-free stage and names four drift types under family-wise error control.
3. A benchmark covering two tabular tasks and two model families, with matched as well as held-out drift mechanisms. It shows that tests built on the definitions of the types carry over to new drift, while a learned rule does not.
4. An end-to-end monitoring pipeline that covers detection, accuracy estimation, root cause analysis, diagnosis, reliability scoring and remediation triage, evaluated on four real drifts with documented causes.

\noindent Section @sec:sota positions the work against existing methods. Sections @sec:method to @sec:results present the pipeline, the experiments and the results, while Section @sec:discussion discusses them and concludes.

# Related work {#sec:sota}

Work related to ours comes from several directions: how drift types are defined, how drift is detected, how label shift is estimated and how accuracy can be estimated without labels. Before reviewing each of them, Table @tab:positioning sets our work beside the methods closest to it. These are black-box shift detection (BBSD), BBSE, confidence-based performance estimation (CBPE), DetectShift and the method of Roschewitz et al.

Table: Capabilities of the closest methods and of ours. A tick marks a capability that the method provides {#tab:positioning}
| Method | Error rate stated | Accuracy estimate | Localizes features | Types named | Concept vs noise | Held-out drift |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| BBSD [@rabanser2019failing] | ✓ | – | limited | – | – | – |
| BBSE [@lipton2018bbse] | ✓ | – | – | prior | – | – |
| CBPE [@kivimaki2025performance] | – | ✓ | – | – | – | – |
| DetectShift [@maiapolo2023detectshift] | ✓ | – | – | needs labels | – | – |
| Roschewitz et al. [@roschewitz2025shiftid] | ✓ | – | – | prior, cov. | – | – |
| Ours | ✓ | ✓ | ✓ | four | ✓ | ✓ |

Each existing method covers one or two of the columns. Roschewitz et al. come closest, separating prior from covariate shift without labels, while DetectShift names types only when the production data are labeled. The paragraphs below look at each line of work in turn.

*Drift types.* Moreno-Torres et al. [@moreno2012unifying] define covariate shift, prior shift and concept shift by the part of the joint distribution of inputs and labels that changes. DetectShift tests for a change in this joint distribution and in each of its parts, $P(X)$, $P(Y)$, $P(X\mid Y)$ and $P(Y\mid X)$ [@maiapolo2023detectshift]. It needs labels for the new data, however, which its authors acknowledge as a limitation. We keep the same definitions, add label noise as a fourth type and ask for labels only in a small audit.

*Drift detection.* Some detectors follow the error rate of the model, for example the drift detection method (DDM) [@gama2004ddm]. They need a label for every prediction and can detect concept drift, but they cannot tell it apart from label noise. Label-free detectors compare the inputs or the model outputs instead. Rabanser et al. [@rabanser2019failing] compared univariate tests, kernel tests [@gretton2012kernel], classifier two-sample tests [@lopezpaz2017c2st] and BBSD on the model outputs. BBSD worked best overall. Each of these tests says that a shift happened, not what type it was. Our pipeline uses such tests as building blocks and goes on to name the type.

*Label shift.* BBSE recovers the new class prior from the confusion matrix of any classifier [@lipton2018bbse]. It assumes that the inputs inside each class stay as they were, which is exactly the property that separates prior shift from covariate shift. Roschewitz et al. [@roschewitz2025shiftid] test this property on medical images. They resample the reference data to the estimated prevalence and attribute the shift to prevalence if the features then stop differing. Our label-free stage follows the same idea. It differs in two ways: it uses importance weights in place of resampling and it puts every label-free decision into one family with a stated error rate.

*Performance estimation without labels.* Average confidence (AC) [@hendrycks2017baseline], difference of confidences (DoC) [@guillory2021predicting], average thresholded confidence (ATC) [@garg2022atc] and CBPE [@kivimaki2025performance] all estimate accuracy from what the model outputs. Each assumes that the link between confidence and accuracy holds in production. Models often stay confident while their accuracy falls under shift [@ovadia2019trust], so the assumption can fail. We report CBPE next to the other three and read it as an upper bound when the assumption breaks.

*Explanation, reliability and benchmarks.* Shapley additive explanations (SHAP) [@lundberg2017unified] attribute a prediction to the input features. Class activation maps (CAM) [@zhou2016cam] do the same for image regions. Out-of-distribution (OOD) scores such as the Isolation Forest [@liu2008isolation] flag unusual inputs, while importance weighting corrects covariate shift [@shimodaira2000; @sugiyama2007; @cortes2010weights]. Folktables [@ding2021retiring] and the Continual LEArning on Real-World Imagery (CLEAR) benchmark [@lin2021clear] provide real shifts, although nobody knows their exact type. Injected shifts give a ground truth [@rabanser2019failing] but may favor the method being tested. Each of these tools serves one stage of our pipeline. Our benchmark holds out drift mechanisms to limit the risk of favoring the tests.

In short, each prior method solves part of the problem. To our knowledge, no published method separates concept drift from label noise with a small label audit. Neither has any type diagnosis been tested on drift mechanisms held out from its design.

# Method {#sec:method}

This section first defines the four drift types precisely and then follows the data through the pipeline introduced in Section @sec:intro. Its input is a deployed model, the labeled data on which it was built and a stream of unlabeled production data, plus a few hundred late labels once they arrive. The stages are those of Fig. @fig:architecture.

Stages A to C bring the data into a common form, test whether anything has changed and estimate how much accuracy the change may cost. Stage D, the core of the paper, names the type of change and points to its likely cause. Stages E and F then act on what was found, first for single predictions and then for the decision to retrain. Only the optional audit in stage D uses production labels. With one exception, every decision in the pipeline is a hypothesis test at the significance level $\alpha=\res{acs-alpha}$. The exception is the population stability index (PSI), which raises an alarm at a conventional threshold. When many tests are run together, the chance of at least one false alarm is held at $\alpha$ by the Holm procedure [@holm1979], its weighted form or its Bonferroni bound.

## Notation and drift types {#sec:types}

To test for a drift type we first have to say exactly what that type changes. A little notation makes this easier. Write $P(X,Y)$ for the distribution of inputs $X$ and labels $Y$ behind the reference data. A production window (a batch of rows from a later period or from another region) is drawn from $Q(X,Y)$. On every row the model outputs a predicted label $\hat y$ together with a confidence $c$, taken as its largest class probability. The four types differ in what changes between $P$ and $Q$. Covariate shift has $Q(X)\neq P(X)$ while $Q(Y\mid X)=P(Y\mid X)$. Prior shift has $Q(Y)\neq P(Y)$ while $Q(X\mid Y)=P(X\mid Y)$. Concept drift has $Q(Y\mid X)\neq P(Y\mid X)$. Label noise is different again: the true distribution does not move at all, yet each label we observe may have been flipped with some probability. Two more terms recur below. An audit means a random sample of $m$ production rows whose labels come in late. A control window is drawn from the reference distribution itself, so no alarm should fire on it. In practice a real window may carry several types at once; Section @sec:discussion comes back to this.

## Reference split, detection and estimation {#sec:detection}

Stage C answers three questions: have the data moved, how much accuracy might the change cost and where in the inputs is it located? All three need a clean reference to compare against. The labeled reference data are therefore split into three disjoint parts, stratified by class: \res{acs-split-pct-train}% for training, \res{acs-split-pct-calibration}% for calibration and \res{acs-split-pct-test}% for testing. The model is fitted on the training part alone. The calibration part is the reference window for every detector and fits the accuracy estimator. The test part gives the reference accuracy and doubles as the control window. Nominal features, such as an occupation code, are treated as categories because their numeric order means nothing. Images are mapped to the \res{clear-dim}-dimensional output of the global average pooling layer of a frozen residual network with 18 layers (ResNet-18) trained on ImageNet [@he2016deep]. Image drift can then be tested with the same tests as tabular drift [@rabanser2019failing].

Six detectors decide whether the inputs or the model outputs have moved. The Kolmogorov–Smirnov (KS) test compares each numeric feature, with a Bonferroni correction over features. PSI raises an alarm at its conventional value of \res{acs-psi-threshold} [@siddiqi2006]. The maximum mean discrepancy (MMD) test [@gretton2012kernel] compares all standardized inputs jointly through a Gaussian kernel, with a permutation p value. The confidence test compares histograms of $c$ with a $\chi^2$ test of homogeneity and pools sparse cells until every expected count reaches \res{const-min-expected} [@cochran1954]. Two further detectors from Rabanser et al. [@rabanser2019failing] act as baselines. BBSD applies a KS test to each class probability. The domain classifier trains gradient boosted trees to tell \res{acs-dc-n} reference rows from as many production rows. An exact binomial test then compares its held-out accuracy with $1/2$ [@lopezpaz2017c2st]. Every permutation p value is given by $(1+b)/(1+B)$, where $b$ of the $B$ permutations reach the observed statistic [@phipson2010].

Labels arrive late, so the accuracy is first estimated from the model's own confidence with CBPE [@kivimaki2025performance]. A map $a(\cdot)$ from confidence to the probability of a correct prediction is fitted by histogram binning on the calibration part. For a window with confidences $c_1$ to $c_n$, the estimate $\hat A$ is given by

$$\hat A = \frac{1}{n}\sum_{i=1}^{n} a(c_i)$$. {#eq:cbpe}

\noindent A confidence bin that holds fewer than \res{const-min-expected} calibration rows cannot give a reliable accuracy, so predictions in such a bin keep their own confidence in Eq. (@eq:cbpe). As baselines, AC, DoC and ATC (with the negative entropy score) are fitted on the same calibration part [@hendrycks2017baseline; @guillory2021predicting; @garg2022atc].

An alarm helps more when it also says where the change sits. Localization tests every feature, with KS for numeric features and the $\chi^2$ homogeneity test for nominal ones, under Holm correction. It reports an effect size between 0 and 1 for each feature: the KS statistic or Cramér's $V$. For nominal features it also gives the share of production rows whose category never occurs in the reference.

## Drift type diagnosis {#sec:diagnosis}

Stage D turns an alarm into one of the four types and thereby into a response. It follows the decision path in Fig. @fig:decision. The questions in the upper row use no labels and separate covariate shift from prior shift. The lower row separates concept drift from label noise. It runs only when no label-free test rejects and an audit is available.

![Decision path that names the drift type. Questions are shown in white boxes and verdicts in gray boxes; the upper row needs no labels and the lower row uses the audit](Fig02.png){#fig:decision width=100}

*Label-free stage.* The first question is whether anything has moved at all. Three blocks of tests answer it: the feature tests, a $\chi^2$ test on the predicted labels and the MMD test. They form one family tested at level $\alpha$ with a weighted Holm procedure [@holm1979]. The weight starts out split evenly, one third per block. Inside the feature block it is divided again among the individual features. A test that rejects hands its weight on to those still waiting, which is how the family-wise error rate survives every label-free decision. In its first step the procedure reduces to ordinary Holm over the three blocks, each feature block entering through its Bonferroni p value. We pool in this way on purpose. A permutation test cannot return a p value below $1/(B+1)$, so without pooling the MMD test would have little chance against dozens of feature tests. If nothing rejects, the stage stops and reports no shift.

A rejection raises the next question: could a change in the class balance alone produce what we see? To find out, BBSE first estimates the new class prior. Let $C_{jk}=P(\hat y=j,y=k)$ on the calibration part and let $\mu_j$ be the share of production predictions that fall in class $j$. The class weights $w_k=Q(Y=k)/P(Y=k)$ are given by the solution of

$$C\,w = \mu$$. {#eq:bbse}

\noindent If the shift really is a pure prior shift, each class keeps its own input distribution. Reweighting every reference row by the weight $w_{y}$ of its class, as given by Eq. (@eq:bbse), ought then to reproduce the production inputs. Checking this is the label shift consistency test, which borrows the prevalence adjustment idea of Roschewitz et al. [@roschewitz2025shiftid]. The feature tests are repeated against the weighted reference, using Kish's effective sample size [@kish1965] and Holm correction. A feature that still differs carries a covariate shift. If no feature differs and the predicted labels have moved, the shift is a prior shift. A prior shift always moves the predicted labels of an informative classifier, so a shift that leaves them in place is called covariate.

*Audit stage.* Concept drift and label noise do not touch the inputs or the model outputs, so only labels can reveal them. The audit draws $m$ late labels and first checks, with a one-sided two-proportion test, whether accuracy has dropped. If it has, the next question is whether the change in errors depends on a feature. To answer it, a logistic model of whether a prediction is correct is fitted on the calibration rows and the audit rows together. Its null form holds \res{const-quantile-bins} confidence bins at reference quantiles, bins of a feature $f$, an audit indicator and the interaction of that indicator with the confidence bins. The alternative adds the interaction of the indicator with the bins of $f$. A likelihood ratio test compares the two for each feature. A nominal category gets its own bin only if it occurs at least $n_{\min}$ times in the audit, where $n_{\min}$ is given by $\lceil 5/\min(e,1-e)\rceil$ and $e$ is the audit error rate. The remaining categories share one bin.

The confidence term is what separates the two types. In a binary task, uniform label noise at rate $r$ makes the probability of a correct prediction equal to $r+(1-2r)\,q(x)$, where $q(x)$ is the model's own probability of being right at $x$. The change therefore depends on $x$ only through $q(x)$, which the confidence bins of the null absorb. Concept drift, by contrast, moves the errors inside a region of some feature. A feature that stays significant after Holm correction therefore points to concept drift. If no feature is significant, the verdict is label noise. Each of the two stages is tested at level $\alpha$, so a window without drift receives a drift verdict with probability at most $2\alpha$.

## Root cause analysis {#sec:rca}

The drift type suggests what kind of fix to consider, but not where the trouble started. Root cause analysis fills that gap by asking which inputs the model now leans on more, or less, than before. The answer narrows the search for a cause without proving one. For tabular models we compute SHAP values [@lundberg2017unified] of the deployed model with its preprocessing and compare the mean absolute attribution of every feature on reference and production rows, each change with a percentile bootstrap interval Bonferroni adjusted over the features. For image models, CAM [@zhou2016cam] highlights the image regions behind the prediction of the linear head.

## Reliability and remediation triage {#sec:triage}

Everything so far speaks about a window as a whole. A monitoring team usually wants two more things from it: to know which individual predictions to doubt and whether a cheap retrain would win the accuracy back. For single predictions we combine three signals, each scaled to lie between 0 and 1: the confidence risk $1-c$, the instability of the prediction under small perturbations of the input and an OOD score that blends an Isolation Forest [@liu2008isolation] with a standardized distance. A logistic regression on the calibration part maps the three signals to a probability of error. We fit it only if the calibration part contains at least ten wrong predictions per signal [@peduzzi1996]. With fewer, the risk falls back to $1-c$.

The triage, for its part, has to judge without production labels whether retraining is worth the trouble. It does so with two probes. The first relies on density ratio weights, which come from a classifier trained to tell reference rows from production rows; the weights are fitted on separate folds and capped at \res{const-weight-clip} times their mean [@cortes2010weights]. A model retrained with them is set against an unweighted model on a held-out \res{const-triage-valfrac}% of the reference, weighted in the same way [@shimodaira2000; @sugiyama2007]. The second probe needs late labels from an earlier window. Where they exist, it retrains on them and checks the result on a held-out part of that same window. A retrain is recommended only if some probe predicts a gain that stays significant after Holm correction across the probes.

# Experimental setup {#sec:setup}

The experiments are built around two questions. First, does the procedure name the type correctly when the truth is known, including for drift it was not designed for? Second, does it behave sensibly on real drift, where the type is unknown but the causes are on record?

*Protocol.* Every setting below was fixed before the evaluation that uses it. The diagnosis was frozen before the held-out design B was run for the first time. A later review of the code found two errors in the diagnosis. The label-free stage had used a gatekeeping rule whose family-wise error rate reached \res{fwer-gate-pct}% at a nominal \res{fwer-alpha-pct}% in a simulation, against \res{fwer-wholm-pct}% for the weighted Holm procedure of Section @sec:diagnosis. The audit had also counted nominal categories over the reference rows and audit rows together. Both errors were fixed without looking at the results and every result was produced again, which changed the verdict in \res{fix-nchanged} of the \res{fix-nwindows} benchmark windows. Permutation tests use \res{acs-mmd-perm} permutations. SHAP explains \res{acs-shap-n} rows per side against \res{acs-shap-bg} background rows. Each real audit uses \res{acs-audit-n} labels from its own random stream. All randomness is seeded, so every result can be repeated exactly. Everything ran on one workstation with a \res{const-cpu-cores}-core processor and a graphics processor, using scikit-learn [@pedregosa2011scikit], SciPy, NumPy, SHAP, OpenCLIP and PyTorch.

## Models

A diagnosis that worked for only one kind of model would be of limited use, so the pipeline monitors two untuned model families. The first is logistic regression (LR) with $L_2$ regularization ($C=1$) on standardized numeric and one-hot encoded nominal features. The second is histogram gradient boosting (GB) [@ke2017lightgbm] from scikit-learn [@pedregosa2011scikit] with default settings, no early stopping and native splits on nominal codes. Codes beyond the 254 most frequent are pooled, which is the limit of the implementation. For CLEAR-10 both models work on the frozen embeddings. SHAP is reported for LR only, since for GB the exact explainer would take hours per window.

## Datasets {#sec:datasets}

The real datasets were chosen because the cause of their drift is documented, which lets us check the verdicts against known events. Table @tab:datasets lists the four of them. Two are census tasks from the American Community Survey (ACS) with data from California (CA), Texas (TX), New York (NY), Florida (FL) and Washington (WA). The other two are a gas sensor array and an image stream.

Table: Datasets, drift windows and reference accuracy {#tab:datasets size=8}
<<gen:tab_datasets>>

Rows gives the smallest and the largest window, Inputs the number of features or embedding dimensions and the last two columns the reference test accuracy of LR and GB.

*ACS Income and ACS Employment.* Both tasks come from the ACS of the United States Census Bureau, as packaged by Folktables [@ding2021retiring]. ACS Income predicts from \res{inc-nfeatures} features whether a person earns more than \$50,000. ACS Employment predicts from \res{emp-nfeatures} features whether a person aged 16 to 90 is employed. CA 2014 is the reference. The temporal windows are CA 2015 to 2019 and 2021 to 2023, as no standard 2020 release exists [@census2021experimental]. The geographic windows are TX, NY, FL and WA in 2014. In 2019 the relationship variable RELP was replaced by RELSHIPP [@census2019pums]. We map it back to RELP with the code labels of the 2018 and 2019 data dictionaries (Appendix A). Five documented changes fall in these years: new occupation codes in 2018 [@census2020occupation], a redesigned relationship question in 2019, a new coding of race answers from 2020 [@census2021race], the pandemic and wage growth against the fixed income threshold.

*Gas sensor array drift.* This dataset from the machine learning repository of the University of California, Irvine (UCI) holds 13,910 measurements of six gases by 16 metal oxide sensors, taken over 36 months in ten batches [@vergara2012gas; @rodriguezlujan2014gas]. Each measurement has eight features per sensor. As the sensors age, their response to the same gas drifts while the labels stay exact. This is a documented change in $P(X\mid Y)$. Batches 1 and 2 form the reference and batches 3 to 10 the windows. Some batches are small, so the number of audit labels for a window of $n$ rows is given by $\min(600,\lfloor n/2\rfloor)$.

*CLEAR-10.* This image stream has ten object classes and a background class, spread over ten time-ordered buckets of about 3,300 images each [@lin2021clear]. Bucket 1 is the reference.

## Injection benchmark {#sec:benchmark-setup}

The type of a real drift is never known for certain, so the diagnosis is graded on drift that we inject ourselves. The benchmark uses the 2014 data of \res{bench-nstates} states (\res{bench-states}) for both ACS tasks. Each state acts as a reference distribution with its own model, split as described above. For each of \res{bench-nseeds} seeds the split, the window and the injection are drawn again, which gives \res{bench-nreps} replicates per configuration. A replicate draws a production window of \res{bench-prodsize} rows and a grading holdout of \res{bench-holdsize} rows from the test part. Each mechanism is injected into both at three intensities. The audit uses \res{bench-audit-n} labels. Proportions carry Wilson intervals [@wilson1927] and means carry bootstrap intervals over replicates.

*Design A* injects the four types in ways that partly match how the tests work. Covariate shift rescales two numeric features (ACS Income: \res{bench-cov-features-inc}) for a random subset of rows. Prior shift drops rows of one class until the positive rate rises by \res{bench-prior-steps}. Concept drift inverts the labels of the \res{bench-concept-steps}% of rows with the highest value of one feature (ACS Income: \res{bench-concept-feature-inc}). Label noise flips a random \res{bench-noise-steps}% of the labels. Each replicate also contains a control window without drift.

*Design B* uses mechanisms that the tests were not built for. Covariate shift becomes selection bias. Each row is kept with a probability given by $\sigma(\beta s(x))$, where $\sigma$ is the logistic function, $s$ is a seeded random score over all inputs and $\beta\in\{\res{bench-b-betas}\}$. The rows stay real and $P(Y\mid X)$ is exactly unchanged. Prior shift lowers the positive rate by \res{bench-b-prior-steps}. Concept drift inverts the labels in the top \res{bench-b-concept-steps}% of a second random score, which marks out an oblique region that no single feature describes. For ACS Income a second concept drift raises the income threshold to \res{bench-b-thresholds}. Label noise is class-conditional: positive labels are flipped to negative at rates of \res{bench-b-noise-steps}%.

## Baselines and ablations {#sec:baselines}

A diagnosis is only worth running if it does better than simpler options. Every method below names one of the five outcomes (no drift or one of the four types) from the same tests and the same audit labels. Three rules stand for current practice. *Input monitoring* reads any input alarm as covariate shift, which is how drift alarms are commonly read. *BBSE first* reads a shift in the predicted labels as prior shift [@lipton2018bbse; @rabanser2019failing] and any other alarm as covariate shift. It is our label-free stage without the consistency test. *Error-rate monitoring* also reads a significant drop in audit accuracy as concept drift, as an error-rate detector would [@gama2004ddm].

The *learned meta-classifier* checks whether a learned rule could replace the tests. It is a GB model trained on nine statistics of each window: the evidence $-\log_{10}p$ of each block test, the share of features with residual shift, the BBSE prior change, the CBPE change, the evidence and size of the drop in audit accuracy and the evidence of the error structure test. In design A it is validated by leaving one state out. In design B it is trained on design A without the state being predicted, so it never sees a held-out mechanism. Three ablations take parts out of our procedure: the MMD block, the confidence term of the audit null and, in a third variant, the confidence bins, which are replaced by cells of predicted class and confidence.

Each method is compared with ours through the per-replicate difference in the share of correctly typed windows, tested by sign-flip permutation (\res{bench-nflips} flips) with Holm correction. Replicates are the unit of analysis because the windows of one replicate share a model and a reference.

# Results {#sec:results}

The benchmark comes first: how often the type is named, whether the procedure carries over to drift it was not designed for, how many audit labels it needs and how well its building blocks work. Real drift follows, then the last two stages, the dashboard and the running time.

## Drift type against baselines {#sec:res-methods}

The most direct test of the diagnosis is how often it names the injected type, compared with the baselines. Table @tab:methods gives this share for every configuration, each with \res{bench-nreps} replicates.

Table: Share of benchmark windows with the correct drift type (%), for each model family, task and design {#tab:methods size=8}
<<gen:tab_methods>>

Inc. and Emp. stand for ACS Income and ACS Employment. A and B are the two designs. An arrow marks a method that differs significantly from ours after Holm correction: a down arrow means that ours is better and an up arrow that ours is worse. The upper block lists the competing methods and the lower block the ablations of our procedure.

With LR on ACS Income, our procedure names the type in \res{b-inc-a-lr-ours-acc}% of design A windows (95% interval \res{b-inc-a-lr-ours-ci}). The best rule baseline reaches \res{b-inc-a-lr-errorratemonitoring-acc}%. The rules are held back by design, since each can name only some of the five outcomes. Over all eight configurations our procedure is significantly better in \res{bench-nbetter} of the \res{bench-ntests} comparisons with a baseline or the learned rule. It is significantly worse in \res{bench-nworse}, \res{bench-worse-cells}.

On design A the learned meta-classifier is the strongest competitor. Validated on states it has not seen, it reaches \res{b-inc-a-lr-metaclassifier-acc}% on ACS Income, above our \res{b-inc-a-lr-ours-acc}%. The held-out mechanisms of design B turn this around. Trained on design A, the meta-classifier drops to \res{b-inc-b-lr-metaclassifier-acc}% on ACS Income and \res{b-emp-b-lr-metaclassifier-acc}% on ACS Employment, while our procedure keeps \res{b-inc-b-lr-ours-acc}% and \res{b-emp-b-lr-ours-acc}%. The learned rule had tied each type to the size and shape of the injected shift. It had learned, for example, that covariate shift means a large shift in two features. It therefore misses selection bias, which moves many features a little. This is the main argument for tests over a learned rule. The tests encode what the drift types are, not what the training examples happened to look like.

The overall rates do not show which types get confused with which. Fig. @fig:confusion breaks the results down by type for LR.

![Injected (rows) and diagnosed (columns) drift types on the benchmark with LR, in counts of windows; darker cells hold a larger share of their row](Fig03.png){#fig:confusion width=100}

A perfect diagnosis would fill only the diagonal. Design B has no control windows, so false alarms are measured on design A. There, most errors sit in the label noise row, where noise is read either as concept drift or as no drift. The control row holds the false alarms. Our procedure raised one on \res{diag-fa-n} of \res{det-ncontrols} control windows (\res{diag-fa-pct}%), \res{diag-fa-labelfree-n} in the label-free stage and \res{diag-fa-audit-n} in the audit. That is below the bound of \res{diag-fa-bound-pct}% derived in Section @sec:diagnosis. In design B the errors gather in the concept and noise rows, for reasons given in Section @sec:res-mechanisms.

The ablations show which parts of the procedure carry the weight. Without the confidence term in the audit null, accuracy on ACS Income design A falls by \res{b-inc-a-lr-noconfidencenull-diffabs} points, because uniform label noise then looks like concept drift. Dropping the MMD block changes little on the benchmark (\res{b-inc-a-lr-nommd-diff} points), whose shifts are visible feature by feature. Its value shows on the image embeddings of Section @sec:res-real. Replacing the confidence bins by cells of predicted class and confidence helps on ACS Employment design B (\res{b-emp-b-lr-classconfidencenull-acc}% against \res{b-emp-b-lr-ours-acc}%) but costs accuracy on ACS Income design A (\res{b-inc-a-lr-classconfidencenull-acc}%). Switching to it now would mean choosing the method after seeing design B. It therefore stays an ablation and a direction for future work.

## Held-out mechanisms {#sec:res-mechanisms}

Design B asks whether the procedure carries over to drift it was not built for. It is the harder of the two tests, since none of its mechanisms shaped any part of the procedure. Table @tab:mechanisms gives the results for each mechanism.

Table: Design B results by drift mechanism {#tab:mechanisms}
<<gen:tab_mechanisms>>

Corr. is the share of windows typed correctly (%) and Drop is the mean true accuracy drop in points; a negative value means that accuracy rose. The income threshold mechanism exists only for ACS Income.

Three of the five mechanisms carry over well. Selection bias is named covariate shift in \res{b-inc-lr-mech-selection-id}% of ACS Income windows with LR, even though no value is distorted and the shift is spread across all features. A lower positive rate is named prior shift in \res{b-inc-lr-mech-priordecrease-id}%. Concept drift in an oblique region, which no single feature bounds, is still recognized in \res{b-inc-lr-mech-conceptoblique-id}%.

The other two mechanisms are harder. A higher threshold relabels some rows in each window, yet model accuracy hardly moves (mean drop \res{b-inc-lr-mech-conceptthreshold-drop} points). With almost nothing lost, the audit stops at its first question and reports no drift in \res{b-inc-lr-mech-conceptthreshold-as-none} of the \res{b-inc-lr-mech-conceptthreshold-n} windows. This is intended, as the procedure looks for drift that costs accuracy and this drift costs almost none. Class-conditional label noise is recognized in only \res{b-inc-lr-mech-classnoise-id}% of ACS Income windows, for two reasons. At low flip rates the loss of accuracy is too small to show up in \res{bench-audit-n} labels. At high rates the errors follow the true class, which is itself correlated with the features, so the error structure test reads the pattern as concept drift. A null model built on confidence alone cannot separate the two, a true limitation. Neither failure involves the label-free stage.

Results on ACS Employment and with GB point the same way. On design A the procedure reaches \res{b-emp-a-lr-ours-acc}% on ACS Employment with LR, while GB brings it to \res{b-inc-a-hgb-ours-acc}% on ACS Income and \res{b-emp-a-hgb-ours-acc}% on ACS Employment. Label noise stays the hardest type there (\res{b-emp-a-lr-id-labelnoise}% of windows). The ranking of the methods survives the switch of model family, as expected for tests that see only the outputs of the model and its errors.

## Size of the delayed audit {#sec:budget}

The audit stage of Section @sec:diagnosis needs late labels. Labels cost money, so it matters how many are enough. This paper uses \res{acs-audit-n} labels throughout. Fig. @fig:budget shows how the share of correctly diagnosed windows changes with the size of the audit on ACS Income design A with logistic regression (LR).

![Share of correctly diagnosed windows on ACS Income design A with LR against the number of audit labels. The shaded bands are 95% Wilson intervals](FigS1.png){#fig:budget width=88}

With 200 labels, concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows and label noise in \res{b-inc-a-lr-budget-labelnoise-200}%. With 600 labels the two rates reach \res{b-inc-a-lr-budget-concept-600}% and \res{b-inc-a-lr-budget-labelnoise-600}%. Going on to 1,000 labels adds little (\res{b-inc-a-lr-budget-concept-1000}% and \res{b-inc-a-lr-budget-labelnoise-1000}%). The 600 labels used in this paper therefore sit where more labels stop paying off. The control windows are diagnosed correctly in the same share of cases at every audit size.

## Detection and accuracy estimation {#sec:res-detection}

The diagnosis rests on the detectors and on the accuracy estimate, so we also check both on the benchmark. Table @tab:detectors gives the alarm rate of each detector for each injected type, pooled over the four design A configurations.

Table: Detector alarm rates on design A by injected type {#tab:detectors}
<<gen:tab_detectors>>

The no drift column is the false alarm rate with its 95% confidence interval (CI). Over \res{det-ncontrols} control windows every interval contains $\alpha=\res{acs-alpha}$ or lies below it. All detectors catch covariate shift and all except PSI also catch most prior shifts. In concept drift and label noise windows the inputs are the same as in the control window of their replicate, so no detector can see them. This is why the audit is needed. Table @tab:estimators turns to the four accuracy estimates and compares them by their mean absolute error against the measured accuracy.

Table: Mean absolute error of the label-free accuracy estimates (points) {#tab:estimators}
<<gen:tab_estimators estimators_short>>

Cov. and Conc. stand for covariate shift and concept drift, Inc. and Emp. for the two ACS tasks. The smallest error in each column is in bold. On design A all four estimates stay within \res{est-bench-none-max} points without drift and within \res{est-bench-covariate-max} points under covariate shift. Under concept drift and label noise every error equals the whole loss, about \res{est-bench-conceptnoise-cbpe} points, because the inputs do not change. Across these \res{est-ncols} comparisons ATC has the smallest error in \res{est-nbest-atc} and CBPE in only \res{est-nbest-cbpe}. On the gas sensor data all four miss by \res{est-gas-best} to \res{est-gas-worst} points on average. In batch 8 the mean confidence of the LR model falls from \res{gas-ref-conf} to \res{gas-b8-conf} and its accuracy to \res{gas-b8-acc}, yet CBPE estimates \res{gas-b8-est}. The estimate is best read as an upper bound on accuracy.

## Real drift {#sec:res-real}

On real data the type of drift is not known, but its causes are on record. Here we ask whether the verdicts agree with those causes and whether the control windows stay quiet. Fig. @fig:timelines shows how accuracy changes over time in all four datasets.

![Measured accuracy of both models and the label-free CBPE estimate on the temporal windows](Fig05.png){#fig:timelines width=120}

C marks the control window. The numbers mark years (ACS), batches (gas sensor) or buckets (CLEAR-10). The gap in the ACS lines is the missing 2020 release.

Before going through the datasets one by one, Table @tab:realsummary sums up the verdicts and the losses for all four of them and for both model families.

Table: Real drift by dataset and model family {#tab:realsummary}
<<code:real_summary>>

Windows counts the drift windows without the control window. Ctrl. alarms is the number of detector alarms on the control window and Sig. drops the number of windows whose accuracy fell significantly. Max. |Δ| is the largest change in accuracy and Est. err. the mean error of the CBPE estimate, both in points. The last two columns count the verdicts of the diagnosis. No real window was named prior shift, concept drift or label noise. Most of the documented causes act on the inputs, from new codes and a redesigned question to aging sensors, so covariate verdicts are what one would expect.

ACS Income shows the clearest trend, so we start there. Its accuracy falls over time for both models, with LR going from \res{inc-ca2015-acc} in 2015 to \res{inc-ca2023-acc} in 2023, while the CBPE estimate falls far less. Table @tab:income lists the details behind the ACS Income panel of Fig. @fig:timelines.

Table: Detection and diagnosis on the ACS Income windows. The alarms are those of the LR model; Conf. is the confidence test and DC the domain classifier {#tab:income size=8}
<<gen:tab_income income_wide>>

Δ is the change in accuracy, in points, against each model's accuracy on the control window. Est. err. is the error of the CBPE estimate. A tick marks an alarm. Type is the verdict of the diagnosis, which is the same for LR and GB in every window (Cov. is covariate shift). Top shifts lists the two features with the largest effect size: occupation (OCCP), place of birth (POBP), relationship (RELP) and race (RAC1P).

Neither model raises an alarm on the control window. Both call CA 2015, whose accuracy did not change significantly, no drift and every other window covariate shift. The documented events can be read off the localization. The 2018 revision of the occupation codes left \res{inc-ca2018-unseen-occp}% of rows with a code that never occurred in 2014. Occupation lost weight in the model as a result (SHAP change \res{inc-ca2018-shap-occp}). Relationship moves in 2019 (effect size \res{inc-ca2019-eff-relp}), when its survey question was redesigned. Race moves from 2021 (effect size \res{inc-ca2021-eff-rac1p}), once the Census Bureau had changed its coding of written race answers [@census2021race]. Wage growth, measured against a fixed income threshold, shows up in the labels instead: their positive share rises from \res{inc-ctrl-posrate} in the control window to \res{inc-ca2023-posrate} in 2023 while the model predicts only \res{inc-ca2023-predposrate}. Part of the 2023 loss comes from a change in what the labels mean, something no label-free test can detect.

The cost of a drift differs widely between datasets. On ACS Employment every window is diagnosed as covariate shift, yet LR accuracy never changes by more than \res{emp-dacc-maxabs} points; relationship (2019) and race (from 2021) shift there as well while the model barely responds. Here an alarm alone would overstate the problem; the accuracy estimate and the audit keep it in proportion. The gas sensor batches all come out as covariate shift too, as they should for aging sensors that alter $P(X\mid Y)$. The largest loss is in batch 8 (\res{gas-b8-dacc} points for LR). BBSE at first takes each gas batch for a prior shift, since the predicted labels move too. The consistency test corrects this: the sensors respond differently to a gas mix that has not changed.

CLEAR-10 drifts more gently: buckets \res{clr-windownums-none} show no drift for either model, while buckets \res{clr-windownums-covariate} show covariate shift. In buckets \res{clr-windownums-mmdonly} no single embedding dimension shifts significantly with LR. Only the MMD test sees the change while the predicted labels stay put, which is why the multivariate block is needed. The only detector alarm on any control window comes from the domain classifier baseline on CLEAR-10 ($p=\res{clr-ctrl-dc-p}$), a false alarm of the kind that $\alpha$ allows.

## Reliability and triage {#sec:res-reliability}

The last two stages act on single predictions and on retraining. The fused risk score is judged by how well it ranks wrong predictions above right ones. Where the fusion is learned, on ACS and CLEAR-10, its area under the receiver operating characteristic curve (AUROC) differs from that of confidence alone by \res{rel-other-diff-min} to \res{rel-other-diff-max} over \res{rel-other-n} windows and by \res{rel-bench-gain-min} to \res{rel-bench-gain-max} on the benchmark. On the gas sensor array the calibration part holds too few wrong predictions (\res{rel-gas-lr-cal-errors} with LR and \res{rel-gas-hgb-cal-errors} with GB), so the risk falls back to confidence. Confidence alone carries most of the information about a single prediction.

For the triage, a retrain truly helps when importance weighting or the latest labeled window raises holdout accuracy significantly. Over \res{rem-n} real settings (Table @tab:remediation), the triage is right in \res{rem-recent-correct} of the \res{rem-recent-n} settings that have an earlier labeled window, because its recent-window probe is checked on real labels.

Table: Remediation triage on the real windows {#tab:remediation size=8}
<<gen:tab_remediation>>

n is the number of windows. Significant gains counts the windows in which a strategy significantly raised holdout accuracy, by importance weighting (IW), retraining on the most recent labeled window (Recent) or retraining on labels of the window itself (Labels); n/a marks settings without an earlier window. Escalated counts the windows in which the triage recommended a retrain, Truly helps those in which a cheap retrain did help and Correct the windows in which the advice was right.

Where an earlier labeled window exists, retraining on it helps in almost every temporal window. The triage escalates in those windows. The geographic windows of the census tasks have no earlier window. There, importance weighting rarely helps. Without such a window the triage relies on importance-weighted validation. It is then right in \res{rem-norecent-correct} of \res{rem-norecent-n} settings, but mostly by advising against a retrain, since one truly helped in only \res{rem-norecent-helps} of them. Most of the remaining wrong verdicts come from CLEAR-10 with LR and from the geographic windows of ACS Employment. On the benchmark the recall of the triage is \res{b-inc-a-lr-triage-recall}%, because importance-weighted validation cannot see gains outside the reference data.

## The monitoring dashboard {#sec:dashboard}

A diagnosis is only useful if the team can read it. Every stage of the pipeline therefore writes its results to one file, which an interactive dashboard presents. Fig. @fig:dashboard shows its overview for ACS Income with LR.

![The overview of the dashboard for ACS Income with LR: dataset, task and model selectors, the headline results and the five steps of the pipeline, each of which opens a detailed view](FigDash1.png){#fig:dashboard width=110}

Fig. @fig:dashtype shows the detailed view of the drift type step.

![The drift type step of the dashboard for ACS Income with LR: for every window, the answer to each question of the decision path in Fig. @fig:decision (filled circle yes, open circle no, small dot not reached) and the resulting verdict, followed by a summary sentence computed from the results](FigDash2.png){#fig:dashtype width=95}

This view applies the decision path of Fig. @fig:decision to the real California (CA) windows. CA 2015 passes every label-free test. The audit then finds no significant drop in accuracy, so the verdict is no drift. In CA 2016, CA 2018 and CA 2019 the predicted labels stay where they were. The feature tests still reject and the shift survives the prior correction, so these windows are covariate shift. All other windows answer yes to every label-free question and are covariate shift as well. Each view of the dashboard opens with the question it answers and closes with a summary sentence of this kind, so a team can follow the diagnosis without reading the code.

## Computational cost {#sec:res-cost}

A monitor has to finish with one window before the next one arrives, so we also timed the pipeline. Table @tab:runtime gives the wall-clock time per window for the stages of Section @sec:method, from the detectors to the reliability scores.

Table: Wall-clock time per window (seconds) {#tab:runtime}
<<code:runtime>>

Median and Max are taken over all windows of a dataset, the control window included. The times leave out model training and, for CLEAR-10, the computation of the image embeddings. No window took longer than \res{icm-time-max} seconds. With LR on the census tasks most of the time goes to the SHAP values of the root cause analysis, which is why GB, for which no SHAP values are computed, runs faster there. On CLEAR-10 and the gas sensor array the diagnosis takes the largest share. Several of its tests run once per input dimension, of which CLEAR-10 has \res{clear-dim} and the gas sensor array 128. Windows of a day, a week or a month leave ample room; a stream that needs a verdict every few seconds would call for cheaper tests.

# Discussion and conclusions {#sec:discussion}

This paper showed that hypothesis tests with a stated error rate can name the drift type, which decides the right response, from label-free tests and a few hundred late labels. On injected drift the procedure beats rules from monitoring practice and the label shift literature and works for both model families. Unlike a learned meta-classifier, it also carries over to held-out drift, because the tests encode the definitions of the types. On real drift it reported no drift on any control window and traced documented events, from new occupation codes to aging sensors.

Several limits apply. Each benchmark window holds a single type, while real windows such as ACS Income 2023 mix several. The four types are also an idealization: sensor aging changes $P(X\mid Y)$ and, through it, $P(Y\mid X)$, yet our procedure reports it as covariate shift. Design B reduces, but cannot remove, the risk that the benchmark favors the tests. The weighted residual tests do not account for the sampling error of the BBSE weights. At several hundred thousand rows almost any shift is significant, so each decision carries an effect size. The audit lets through drift that does not hurt accuracy and often mistakes class-conditional label noise for concept drift. Deep models trained end to end, text and streaming data remain untested. The next steps are an audit conditioned on the full model output, a model of the sampling error of the BBSE weights and benchmark windows that mix several types.

# Appendix A. Relationship codes across the 2019 redesign {#sec:relp -}

The ACS windows run from 2014 to 2023, but one of their features changed its coding halfway through. From 2019 the Census Bureau replaced the relationship variable RELP with RELSHIPP, whose codes split spouses and partners by sex [@census2019pums]. To compare windows before and after 2019, we map the RELSHIPP codes back to RELP by matching the code labels of the 2018 and 2019 data dictionaries. Table @tab:relp lists the mapping as the code applies it.

Table: Mapping from RELSHIPP (2019 on) back to RELP (2014 to 2018) {#tab:relp size=8}
<<code:relp_wide>>

RELP 11 (roomer or boarder) has no successor, so it never occurs from 2019 on. The loss of this category is itself a documented change that the localization can pick up.

# Disclosure of Interests {-}

The authors have no competing interests to declare that are relevant to the content of this article.

# References {-}
