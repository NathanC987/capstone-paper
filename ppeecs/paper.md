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

\noindent Section @sec:sota reviews related work and Section @sec:method describes the pipeline. Sections @sec:setup and @sec:results report the experiments, Section @sec:discussion discusses their limits and Section @sec:conclusion concludes.

# State of the art {#sec:sota}

Table @tab:positioning compares our work with the closest existing methods: black-box shift detection (BBSD), BBSE, confidence-based performance estimation (CBPE), DetectShift and the method of Roschewitz et al. The paragraphs after it review what each group of related work offers and what it leaves open.

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

*Drift detection.* Detectors that track the error rate, such as the drift detection method (DDM) [@gama2004ddm], need a label for every prediction. They can detect concept drift but cannot distinguish it from label noise. Label-free detectors instead compare the inputs or the model outputs. Rabanser et al. [@rabanser2019failing] compared univariate tests, kernel tests [@gretton2012kernel], classifier two-sample tests [@lopezpaz2017c2st] and BBSD and found that BBSD worked best overall. All of them indicate that a shift has occurred but not of which type.

*Label shift.* BBSE recovers the new class prior from the confusion matrix of any classifier [@lipton2018bbse]. It assumes that the inputs within each class do not change, which is precisely the assumption that separates prior shift from covariate shift. Roschewitz et al. [@roschewitz2025shiftid] test this assumption on medical images by resampling the reference data to the estimated prevalence. Our label-free stage builds on the same idea but uses importance weights instead of resampling and places every label-free decision in one family with a stated error rate.

*Performance estimation without labels.* Average confidence (AC) [@hendrycks2017baseline], difference of confidences (DoC) [@guillory2021predicting], average thresholded confidence (ATC) [@garg2022atc] and CBPE [@kivimaki2025performance] estimate accuracy from model outputs. Each assumes that the relationship between confidence and accuracy carries over to production, which can fail because models often stay confident as their accuracy falls [@ovadia2019trust].

*Explanation, reliability and benchmarks.* Shapley additive explanations (SHAP) [@lundberg2017unified] and class activation maps (CAM) [@zhou2016cam] attribute predictions to features or image regions. Out-of-distribution (OOD) scores such as the Isolation Forest [@liu2008isolation] flag unusual inputs, while importance weighting corrects covariate shift [@shimodaira2000; @sugiyama2007; @cortes2010weights]. Folktables [@ding2021retiring] and CLEAR [@lin2021clear] provide real shifts of unknown type, while injected shifts supply a ground truth [@rabanser2019failing] but risk favoring the method under test. To our knowledge, no published method separates concept drift from label noise with a small label audit. Nor has any type diagnosis been evaluated on drift mechanisms held out from its design.

# Method {#sec:method}

The pipeline is designed for a team that has a deployed model, the labeled data on which it was built and a stream of unlabeled production data. Nothing else is required, although a few hundred late labels sharpen the diagnosis once they arrive. Fig. @fig:architecture gives an overview of the stages. Stages A to C test for change and estimate its cost, stage D names the drift type and its likely cause, while stages E and F act on single predictions and on retraining.

![Stages of the monitoring pipeline, from the inputs (A) to the advice on retraining (F)](Fig01.png){#fig:architecture width=81.6}

Only the optional audit in stage D uses production labels. Apart from the population stability index (PSI), which alarms at its conventional threshold, every decision is a hypothesis test at the significance level $\alpha=\res{acs-alpha}$. The family-wise error rate is controlled by the Holm procedure [@holm1979], its weighted form or its Bonferroni bound.

## Notation and drift types {#sec:types}

The tests require a precise statement of what each type of drift changes. The reference data are drawn from a distribution $P(X,Y)$ over inputs $X$ and labels $Y$. A production window is a batch of rows drawn from $Q(X,Y)$. The model returns a predicted label $\hat y$ and a confidence $c$, its largest class probability. Covariate shift has $Q(X)\neq P(X)$ while $Q(Y\mid X)=P(Y\mid X)$. Prior shift has $Q(Y)\neq P(Y)$ while $Q(X\mid Y)=P(X\mid Y)$. Concept drift has $Q(Y\mid X)\neq P(Y\mid X)$. Under label noise the true distribution stays the same, but each observed label differs from the true one with some probability. An audit is a random sample of $m$ production rows whose labels arrive late. A control window is drawn from the reference distribution itself and should raise no alarm.

## Detection and accuracy estimation {#sec:detection}

Stage C asks whether the data have moved, how much accuracy the change might cost and where it is located. The labeled reference data are split, stratified by class, into \res{acs-split-pct-train}% for training, \res{acs-split-pct-calibration}% for calibration and \res{acs-split-pct-test}% for testing. The calibration part is the reference window for every detector and fits the accuracy estimator, while the test part gives the reference accuracy and acts as the control window. Images are mapped to the \res{clear-dim}-dimensional embedding of a frozen residual network with 18 layers (ResNet-18) [@he2016deep], so the same tests apply [@rabanser2019failing].

Six detectors decide whether the inputs or the model outputs have moved. The Kolmogorov–Smirnov (KS) test is applied to each numeric feature with a Bonferroni correction. PSI alarms at \res{acs-psi-threshold} [@siddiqi2006]. The maximum mean discrepancy (MMD) test [@gretton2012kernel] is a permutation test on all standardized inputs jointly. The confidence test compares histograms of $c$ with a $\chi^2$ test. BBSD and a domain classifier, which separates \res{acs-dc-n} reference rows from as many production rows with gradient boosted trees, serve as baselines [@rabanser2019failing; @lopezpaz2017c2st].

Because labels arrive late, accuracy is first estimated from the model's own confidence with CBPE [@kivimaki2025performance]. A map $a(\cdot)$ from confidence to the probability of a correct prediction is fitted by histogram binning on the calibration part. The estimate $\hat A$ for a window with confidences $c_1$ to $c_n$ is given by

$$\hat A = \frac{1}{n}\sum_{i=1}^{n} a(c_i)$$. {#eq:cbpe}

\noindent Predictions in a confidence bin with fewer than \res{const-min-expected} calibration rows keep their own confidence in Eq. (@eq:cbpe). AC, DoC and ATC are fitted on the same calibration part as baselines [@hendrycks2017baseline; @guillory2021predicting; @garg2022atc]. Localization then tests every feature with KS (numeric) or $\chi^2$ (nominal) under Holm correction and reports an effect size in $[0,1]$, the KS statistic or Cramér's $V$.

## Drift type diagnosis {#sec:diagnosis}

Stage D turns an alarm into one of the four types, each with its own response, along the decision path in Fig. @fig:decision. The upper row of questions uses no labels and separates covariate from prior shift. The lower row separates concept drift from label noise and runs only when no label-free test rejects and an audit is available.

![Decision path that names the drift type. Questions are shown in white boxes and verdicts in gray boxes; the upper row needs no labels and the lower row uses the audit](Fig02.png){#fig:decision width=83.5}

*Label-free stage.* Three blocks of tests ask whether anything has moved: the feature tests, a $\chi^2$ test on the predicted labels and the MMD test. They form one family tested at level $\alpha$ with a weighted Holm procedure [@holm1979]. The blocks receive equal weight, which the feature block divides among its features. The weight of a rejected test passes to the remaining tests. If a block rejects, the diagnosis asks whether a change in the class balance alone explains the shift. Let $C_{jk}=P(\hat y=j,y=k)$ on the calibration part and let $\mu_j$ be the share of production predictions in class $j$. The class weights $w_k = Q(Y=k)/P(Y=k)$ are given by the solution of

$$C\,w = \mu$$. {#eq:bbse}

\noindent Under a pure prior shift the inputs within each class keep their distribution, so reweighting each reference row by $w_{y}$ from Eq. (@eq:bbse) should reproduce the production inputs. This consistency test follows the prevalence adjustment of Roschewitz et al. [@roschewitz2025shiftid]. The feature tests are repeated against the reweighted reference with Holm correction. Any feature that still differs carries a covariate shift. If none differs and the predicted labels have moved, the shift is a prior shift.

*Audit stage.* Concept drift and label noise leave the inputs and the model outputs unchanged, so only labels can reveal them. The audit draws $m$ late labels and first checks with a one-sided two-proportion test whether accuracy has fallen. If it has, a logistic model of whether a prediction is correct is fitted on the calibration and audit rows together. Its null form contains \res{const-quantile-bins} confidence bins, bins of a feature $f$, an audit indicator and the interaction of the indicator with the confidence bins. The alternative adds the interaction of the indicator with the bins of $f$ and is compared with the null by a likelihood ratio test for each feature.

The confidence term separates the two types. In a binary task, uniform label noise at rate $r$ makes the probability of a correct prediction equal to $r+(1-2r)\,q(x)$, where $q(x)$ is the model's own probability of being right at $x$. The change thus depends on $x$ only through $q(x)$. The confidence bins of the null absorb this change. Concept drift instead shifts the errors within a region of some feature, so a feature that remains significant after Holm correction indicates concept drift and no significant feature indicates label noise. Because each stage is tested at level $\alpha$, a window without drift receives a drift verdict with probability at most $2\alpha$.

## Root cause, reliability and triage {#sec:rca}

Knowing the type tells a team what to do, while root cause analysis tells it where to look. For tabular models we compare the mean absolute SHAP value [@lundberg2017unified] of each feature between reference and production rows, with Bonferroni-adjusted bootstrap intervals. For images, CAM shows which regions support the prediction [@zhou2016cam]. Two practical questions remain after the window-level tests. For single predictions, a logistic regression fitted on the calibration part combines the confidence risk $1-c$, an OOD score from an Isolation Forest [@liu2008isolation] and the instability under small perturbations into a probability of error. For retraining, the triage compares a model trained with truncated density ratio weights against an unweighted one on an importance-weighted holdout [@shimodaira2000; @sugiyama2007; @cortes2010weights] and, when an earlier labeled window exists, a model retrained on it. A retrain is recommended when a predicted gain is significant after Holm correction.

# Experimental setup {#sec:setup}

The experiments ask two questions. Does the procedure name the type correctly when the truth is known, including for drift it was not designed for? And does it behave sensibly on real drift with documented causes? All settings were fixed before the evaluation that uses them. The diagnosis was frozen before the held-out design B was first run. A later code review found two errors in the diagnosis. Both were corrected without regard to the results and every result was regenerated (Section @s:sec:protocol of the Supplement). All randomness is seeded, so every result repeats exactly.

## Models and datasets

Since the procedure should not depend on one kind of model, the pipeline monitors two untuned model families. The first is logistic regression (LR) with $L_2$ regularization on standardized numeric and one-hot nominal features. The second is histogram gradient boosting (GB) [@ke2017lightgbm] from scikit-learn [@pedregosa2011scikit] with default settings.

Four datasets contain drift with a documented cause (Table @s:tab:datasets in the Supplement). ACS Income and ACS Employment come from the American Community Survey (ACS), as packaged by Folktables [@ding2021retiring]. With California (CA) 2014 as the reference, the windows are CA 2015 to 2019, CA 2021 to 2023 and four other states in 2014. Documented changes include new occupation codes in 2018 [@census2020occupation], a redesigned relationship question in 2019, a new coding of race answers from 2020 [@census2021race] and wage growth against the fixed income threshold. The gas sensor array drift data hold 13,910 measurements of six gases by 16 metal oxide sensors over 36 months [@vergara2012gas; @rodriguezlujan2014gas]. As the sensors age their response drifts while the labels stay exact, a documented change in $P(X\mid Y)$. CLEAR-10 is an image stream of ten time-ordered buckets [@lin2021clear].

## Injection benchmark

Real drift has no known type, so the diagnosis is graded on injected drift in the 2014 data of \res{bench-nstates} states for both ACS tasks. For each of \res{bench-nseeds} seeds the split, the window and the injection are redrawn, which gives \res{bench-nreps} replicates per configuration. Each replicate draws a production window of \res{bench-prodsize} rows, injects each mechanism at three intensities and uses \res{bench-audit-n} audit labels. *Design A* injects the four types in ways that partly match the tests: rescaled numeric features, rows of one class dropped, labels inverted for the rows with the highest value of one feature and uniformly flipped labels, plus a control window without drift. *Design B* uses mechanisms the tests were not designed for: selection bias with a probability given by $\sigma(\beta s(x))$ for a random score $s$ over all inputs, a lower positive rate, labels inverted in an oblique region of a second random score, a raised income threshold and class-conditional label noise. Section @s:sec:benchmark of the Supplement lists every parameter.

## Baselines and ablations {#sec:baselines}

Every method names one of five outcomes (no drift or one of the four types) from the same tests and audit labels. *Input monitoring* reads any input alarm as covariate shift. *BBSE first* reads a shift in the predicted labels as prior shift [@lipton2018bbse; @rabanser2019failing] and any other alarm as covariate shift. *Error-rate monitoring* also reads a significant audit accuracy drop as concept drift [@gama2004ddm]. The *learned meta-classifier* is a GB model on nine test statistics of each window. It is validated by leaving one state out in design A and is trained on design A for design B, so it never sees a held-out mechanism. Three ablations remove the MMD block, remove the confidence term from the audit null or replace the confidence bins by cells of predicted class and confidence. Our procedure is compared with each method by the per-replicate difference in correctly typed windows, tested by sign-flip permutation (\res{bench-nflips} flips) with Holm correction.

# Results {#sec:results}

The benchmark results come first, followed by real drift.

## Drift type against baselines {#sec:res-methods}

The central question is how often each method names the injected type, which Table @tab:methods answers for every configuration.

Table: Share of benchmark windows with the correct drift type (%). Inc. and Emp. denote ACS Income and ACS Employment, A and B the two designs. An arrow marks a significant difference from ours after Holm correction: down means ours is better, up means ours is worse {#tab:methods}
<<gen:tab_methods stack_models_main>>

With LR on ACS Income, our procedure names the type in \res{b-inc-a-lr-ours-acc}% of design A windows (95% interval \res{b-inc-a-lr-ours-ci}), compared with at most \res{b-inc-a-lr-errorratemonitoring-acc}% for a rule baseline, since each rule can name only some of the five outcomes. Across all eight configurations our procedure is significantly better in \res{bench-nbetter} of the \res{bench-ntests} comparisons with a baseline or the learned rule and significantly worse in \res{bench-nworse}, \res{bench-worse-cells}.

The learned meta-classifier is the strongest competitor on design A, where it reaches \res{b-inc-a-lr-metaclassifier-acc}% on ACS Income. On the held-out mechanisms of design B the picture reverses: it falls to \res{b-inc-b-lr-metaclassifier-acc}% on ACS Income and \res{b-emp-b-lr-metaclassifier-acc}% on ACS Employment, while our procedure retains \res{b-inc-b-lr-ours-acc}% and \res{b-emp-b-lr-ours-acc}%. The learned rule had tied each type to the size and shape of the injected shift. For example, it associated covariate shift with a large shift in two features and therefore misses selection bias, which moves many features slightly. The tests encode the definitions of the drift types instead.

The overall rates hide which types are confused with which, so Fig. @fig:confusion shows this breakdown for LR.

![Injected (rows) and diagnosed (columns) drift types on the benchmark with LR, in counts of windows; darker cells hold a larger share of their row. A perfect result fills only the diagonal](Fig03.png){#fig:confusion width=83.5}

In design A most errors fall in the label noise row, where noise is read as concept drift or as no drift. Our procedure raised false alarms on \res{diag-fa-n} of \res{det-ncontrols} control windows (\res{diag-fa-pct}%), below the bound of \res{diag-fa-bound-pct}% derived in Section @sec:diagnosis. In design B the errors concentrate in the concept and noise rows, for reasons given in Section @sec:res-mechanisms.

The ablations show which parts matter (Table @s:tab:methods in the Supplement). Removing the confidence term from the audit null costs \res{b-inc-a-lr-noconfidencenull-diffabs} points on ACS Income design A, because uniform label noise then looks like concept drift. Removing the MMD block makes little difference on the benchmark (\res{b-inc-a-lr-nommd-diff} points), but it matters on the image embeddings of Section @sec:res-real. Class and confidence cells help on ACS Employment design B (\res{b-emp-b-lr-classconfidencenull-acc}% against \res{b-emp-b-lr-ours-acc}%) but cost accuracy on ACS Income design A. Adopting them now would mean choosing the method after seeing design B, so they remain an ablation.

## Held-out mechanisms {#sec:res-mechanisms}

Design B is the stronger test, since no part of the procedure was shaped by its mechanisms (Table @s:tab:mechanisms in the Supplement). Selection bias is identified as covariate shift in \res{b-inc-lr-mech-selection-id}% of ACS Income windows with LR, although the shift spreads over all features. A lower positive rate is identified as prior shift in \res{b-inc-lr-mech-priordecrease-id}% and concept drift in an oblique region in \res{b-inc-lr-mech-conceptoblique-id}%.

Two mechanisms do not transfer. Raising the income threshold barely changes accuracy (mean drop \res{b-inc-lr-mech-conceptthreshold-drop} points), so the audit reports no drift in \res{b-inc-lr-mech-conceptthreshold-as-none} of the \res{b-inc-lr-mech-conceptthreshold-n} windows. Class-conditional label noise is identified in only \res{b-inc-lr-mech-classnoise-id}% of ACS Income windows. At low rates the accuracy drop is too small for \res{bench-audit-n} labels. At high rates the errors follow the true class, which correlates with the features, so the error structure test reads the pattern as concept drift. Both failures lie in the audit rather than in the label-free stage. The same patterns hold for ACS Employment and for GB: on design A our procedure reaches \res{b-emp-a-lr-ours-acc}% on ACS Employment with LR and, with GB, \res{b-inc-a-hgb-ours-acc}% on ACS Income and \res{b-emp-a-hgb-ours-acc}% on ACS Employment.

## Detection and accuracy estimation {#sec:res-detection}

Over \res{det-ncontrols} control windows, the false alarm interval of every detector contains $\alpha$ or lies below it (Table @s:tab:detectors in the Supplement). Every detector catches covariate shift and all except PSI also catch most prior shifts. Concept drift and label noise share their inputs with the control window, so no detector can see them. Among the accuracy estimates, ATC has the smallest mean absolute error in \res{est-nbest-atc} of \res{est-ncols} comparisons and CBPE in only \res{est-nbest-cbpe}. In gas batch 8 the LR model's accuracy falls to \res{gas-b8-acc}, yet CBPE estimates \res{gas-b8-est}, so the estimate is best read as an upper bound.

## Real drift {#sec:res-real}

Real drift has no known type, but its causes are documented. Fig. @fig:timelines shows how accuracy evolves in all four datasets.

![Measured accuracy of both models and the label-free CBPE estimate on the temporal windows. C marks the control window, the numbers mark years (ACS), batches (gas sensor) or buckets (CLEAR-10) and the gap in the ACS lines marks the missing 2020 release](Fig04.png){#fig:timelines width=83.5}

The control windows stay quiet: the only detector alarm on a control window comes from the domain classifier baseline on CLEAR-10 ($p=\res{clr-ctrl-dc-p}$). On ACS Employment every window is diagnosed as covariate shift, yet accuracy changes by at most \res{emp-dacc-maxabs} points with LR, so the accuracy estimate and the audit put the alarm in proportion. Every gas sensor batch is also diagnosed as covariate shift, matching the known cause of aging sensors, with an accuracy change of \res{gas-b8-dacc} points in batch 8. On CLEAR-10, buckets \res{clr-windownums-mmdonly} shift only in the MMD test, which shows why the multivariate block is needed.

ACS Income shows the clearest trend, with LR accuracy falling from \res{inc-ca2015-acc} in 2015 to \res{inc-ca2023-acc} in 2023 while the CBPE estimate falls much less (Table @s:tab:income in the Supplement). CA 2015 is diagnosed as no drift and every later window as covariate shift. The documented events appear in the localization. After the 2018 occupation revision, \res{inc-ca2018-unseen-occp}% of rows carry a code never seen in 2014. Relationship shifts in 2019 (effect size \res{inc-ca2019-eff-relp}) and race from 2021 (\res{inc-ca2021-eff-rac1p}). The share of positive labels rises from \res{inc-ctrl-posrate} to \res{inc-ca2023-posrate} in 2023, while the model predicts only \res{inc-ca2023-predposrate}, so part of the 2023 loss is a change in the labeling rule that no label-free test can see.

## Reliability and triage {#sec:res-reliability}

The last two stages are judged by how well the risk score ranks wrong predictions and how often the retraining advice is right. Where the risk fusion is learned, its area under the receiver operating characteristic curve (AUROC) differs from that of confidence alone by \res{rel-other-diff-min} to \res{rel-other-diff-max} over \res{rel-other-n} windows, so confidence already carries most of the information about a single prediction. The triage is right in \res{rem-recent-correct} of the \res{rem-recent-n} real settings that have an earlier labeled window. Without one it is right in \res{rem-norecent-correct} of \res{rem-norecent-n}, mostly by advising against retraining. Its benchmark recall is \res{b-inc-a-lr-triage-recall}%, because importance-weighted validation cannot see gains outside the reference data.

# Discussion {#sec:discussion}

A diagnosis built from tests of the type definitions transfers to drift it was not designed for, whereas a learned rule does not. The cost is a small label audit, needed only for concept drift and label noise. Several limitations qualify these findings. Each benchmark window contains a single type, while real windows such as ACS Income 2023 mix several. The four types are also an idealization: sensor aging changes $P(X\mid Y)$ and, through it, $P(Y\mid X)$, yet the procedure reports it as covariate shift. Design B reduces, but cannot eliminate, the risk that the benchmark favors the tests. The weighted residual tests ignore the sampling error of the BBSE weights. With hundreds of thousands of rows even small shifts become significant, which is why effect sizes are reported next to every decision. Deep models trained end to end, text and streaming data are not covered.

# Conclusions {#sec:conclusion}

We showed that the drift type, which determines the response, can be identified by hypothesis tests with a stated error rate from label-free tests and a few hundred late labels. On injected drift the procedure outperforms rules from monitoring practice and the label shift literature, works for both model families and, unlike a learned meta-classifier, transfers to held-out drift. On real drift it reported no drift on any control window and traced documented events, from new occupation codes to aging sensors. Future work will condition the audit on the full model output, model the sampling error of the BBSE weights and test mixed drift.

# Acknowledgement {-}

This research received no external funding.

# References {-}
