# Implementation of the Proposed System {#ch:impl}

This chapter describes how the design of Chapter @ch:design was built. It explains the development method first, then gives the algorithms of each module with their formulas, flowcharts and pseudocode and ends with the datasets: where they come from, how they were prepared and how they were used.

## Methodology Employed for Development {#sec:method}

The system was developed incrementally over the two semesters, one stage of the pipeline at a time. Each stage was first built as a working prototype, shown in the dashboard and discussed at a mentor review, then hardened with tests and rerun on all datasets. This order meant that a complete, if rough, system existed early and every later improvement could be judged on real outputs.

Four practices ran through the whole development.

- **A fixed protocol.** Every setting of an experiment, from the significance level to the audit size, was fixed before the evaluation that uses it. The diagnosis was frozen before the held-out benchmark design was run for the first time, so that design could not be tuned to it.
- **Generated results.** Every study writes a JSON report and a build script turns the reports into named result values, tables and figures. Documents cite results only through these names, so a number cannot be mistyped or left stale.
- **Seeded randomness.** Every random choice (data splits, permutations, injections, samples for explanations) takes a seed, so every result can be repeated exactly.
- **Tests and review.** Statistical routines were checked against reference implementations and by simulation of their error rates. A code review late in the project found two errors in the diagnosis; both were fixed without looking at the results and every result was produced again.

The code is written in Python 3.14 and organized as the package of Section @sec:modules, with two Git repositories: one for the code and one for the paper and this report. Long runs, such as the benchmark, were scheduled one at a time with a capped number of parallel workers.

A key implementation choice concerns the reference data. They are split into three disjoint parts, stratified by class: \res{acs-split-pct-train}% for training, \res{acs-split-pct-calibration}% for calibration and \res{acs-split-pct-test}% for testing. The model is fitted on the training part alone. The calibration part is the reference window for every detector and fits the accuracy estimator and the test part gives the reference accuracy and doubles as a control window on which no alarm should fire. Two model families are monitored, both untuned: logistic regression (LR) with $L_2$ regularization ($C=1$) on standardized numeric and one-hot encoded nominal features and histogram gradient boosting (GB) [@ke2017lightgbm] from scikit-learn [@pedregosa2011scikit] with default settings and native splits on nominal codes.

## Algorithms and Flowcharts for Modules Developed {#sec:algorithms}

The algorithms follow the stages of the block diagram. Algorithm @alg:window gives the overall processing of one production window and the subsections below describe each step.

```Processing of one production window {#alg:window}
Input:  model M, calibration part R, production window W, optional audit (X_a, y_a)
Output: report for W
1  validate the schema and feature types of W against R
2  predict labels and class probabilities of M on W
3  run the detectors (KS, PSI, MMD, confidence test) of W against R
4  estimate the accuracy of M on W from its confidences (CBPE)
5  localize: test every feature, record effect sizes and unseen categories
6  verdict ← label-free diagnosis (Algorithm @alg:labelfree)
7  if verdict = no shift and an audit is available then
8      verdict ← audit diagnosis (Algorithm @alg:audit)
9  explain the change: SHAP for tabular models, CAM for image models
10 score the risk of error of every prediction
11 triage: would a cheap retrain help? (Algorithm @alg:triage)
12 write all results, with the time of each stage, to the report
```

### Detection and Localization {#sec:alg-detection}

Detection decides whether a window differs from the calibration part and localization says where the difference sits. Fig. @fig:flow-detection shows the flow.

![Flowchart of detection, accuracy estimation and localization for one window](flow_detection.png){#fig:flow-detection width=78}

The window is validated and scored by the model, the detectors and the accuracy estimate are run and if any test is significant after correction the features are localized. The results pass to the diagnosis in either case. Four detectors are used by the diagnosis and two more act as baselines.

The **Kolmogorov–Smirnov (KS) test** compares each numeric feature. With $F_P$ and $F_Q$ the empirical distribution functions of the feature in the calibration part and in the window, its statistic is given by

$$D = \sup_x \left| F_P(x) - F_Q(x) \right|$$ {#eq:ks}

\noindent Eq. (@eq:ks) is evaluated for every numeric feature, with a Bonferroni correction over the features that keeps the detector's error rate at α. The **population stability index (PSI)** compares the shares $p_b$ and $q_b$ of the reference and the window in $B$ bins of each feature. It is given by

$$\mathrm{PSI} = \sum_{b=1}^{B} {(q_b - p_b)\ln\frac{q_b}{p_b}}$$ {#eq:psi}

\noindent An alarm is raised when the index of Eq. (@eq:psi) exceeds its conventional value of \res{acs-psi-threshold} [@siddiqi2006]. The **maximum mean discrepancy (MMD)** test compares all standardized inputs jointly [@gretton2012kernel]. With a Gaussian kernel $k(x,y)=\exp\left(-\|x-y\|^2/2\sigma^2\right)$, reference rows $x_1$ to $x_m$ and window rows $y_1$ to $y_n$, its statistic is given by

$$\mathrm{MMD}^2 = \frac{1}{m^2}\sum_{i,j} k(x_i,x_j) + \frac{1}{n^2}\sum_{i,j} k(y_i,y_j) - \frac{2}{mn}\sum_{i,j} k(x_i,y_j)$$ {#eq:mmd}

\noindent The p value of Eq. (@eq:mmd) comes from \res{acs-mmd-perm} random permutations of the pooled rows. A permutation p value is given by $(1+b)/(1+B)$, where $b$ of the $B$ permutations reach the observed statistic [@phipson2010]. The **confidence test** compares histograms of the model's top-class confidence $c$ in the two samples with the chi-square test of homogeneity, whose statistic over cells with observed counts $O_k$ and expected counts $E_k$ is given by

$$\chi^2 = \sum_{k} \frac{(O_k - E_k)^2}{E_k}$$ {#eq:chi2}

\noindent Before Eq. (@eq:chi2) is evaluated, sparse cells are pooled until every expected count reaches \res{const-min-expected} [@cochran1954]. Two baselines from Rabanser et al. [@rabanser2019failing] complete the set: black-box shift detection (BBSD), which applies a KS test to each class probability. The other is a domain classifier, which trains gradient boosted trees to tell \res{acs-dc-n} reference rows from as many window rows and compares its held-out accuracy with $1/2$ by an exact binomial test [@lopezpaz2017c2st].

**Localization** tests every feature on its own, with KS for numeric features and the chi-square test for nominal ones, under Holm correction [@holm1979]. Holm's procedure orders the $m$ p values from smallest to largest and rejects them one by one while the $i$-th smallest is at most $\alpha/(m-i+1)$, which holds the chance of any false rejection at α. Each feature also gets an effect size between 0 and 1: the KS statistic $D$ or Cramér's $V$, given by

$$V = \sqrt{\frac{\chi^2}{n\,(k-1)}}$$ {#eq:cramer}

\noindent where $n$ is the number of rows and $k$ the number of categories, so that Eq. (@eq:cramer) is 0 when the category shares agree and grows towards 1 as they separate. For nominal features the share of window rows whose category never occurs in the reference is reported as well, which is how new occupation codes show up.

### Accuracy Estimation {#sec:alg-estimation}

Labels arrive late, so the accuracy is first estimated from the model's own confidence with confidence-based performance estimation (CBPE) [@kivimaki2025performance]. A map $a(\cdot)$ from confidence to the probability of a correct prediction is fitted by histogram binning on the calibration part. For a window with confidences $c_1$ to $c_n$, the estimate $\hat A$ is given by

$$\hat A = \frac{1}{n}\sum_{i=1}^{n} a(c_i)$$. {#eq:cbpe}

\noindent Three alternatives to Eq. (@eq:cbpe) are fitted on the same calibration part for comparison: average confidence (AC) [@hendrycks2017baseline], difference of confidences (DoC) [@guillory2021predicting] and average thresholded confidence (ATC) with the negative entropy score [@garg2022atc]. All four assume that the link between confidence and accuracy survives the shift, so the estimate is read as an upper bound when that assumption fails.

### Drift Type Diagnosis {#sec:alg-diagnosis}

The diagnosis turns an alarm into one of the four drift types and thereby into a response. Fig. @fig:decision shows its decision path.

![Decision path that names the drift type. Questions are shown in white boxes and verdicts in gray boxes; the upper row needs no labels and the lower row uses the audit](decision_path.png){#fig:decision width=125}

The questions in the upper row use no labels and separate covariate shift from prior shift. The lower row separates concept drift from label noise and runs only when no label-free test rejects and an audit is available. Each stage is tested at level α, so a window without drift receives a drift verdict with probability at most 2α.

**Label-free stage.** The first question is whether anything has moved at all. Three blocks of tests answer it: the feature tests, a chi-square test on the predicted labels and the MMD test. They form one family tested at level α with a weighted Holm procedure. The weight starts out split evenly, one third per block and inside the feature block it is divided again among the individual features. A test that rejects hands its weight on to the tests still waiting, which is how the family-wise error rate survives every label-free decision. Pooling in this way matters because a permutation test cannot return a p value below $1/(B+1)$; without pooling, the MMD test would have little chance against dozens of feature tests.

A rejection raises the next question: could a change in the class balance alone produce what we see? Black-box shift estimation (BBSE) [@lipton2018bbse] first estimates the new class prior. Let $C_{jk}=P(\hat y=j,y=k)$ on the calibration part and let $\mu_j$ be the share of window predictions that fall in class $j$. The class weights $w_k=Q(Y=k)/P(Y=k)$ are given by the solution of

$$C\,w = \mu$$. {#eq:bbse}

\noindent If the shift really is a pure prior shift, each class keeps its own input distribution and reweighting every reference row by the weight of its class, as given by Eq. (@eq:bbse), ought to reproduce the window's inputs. The label shift consistency test checks this, borrowing the prevalence adjustment idea of Roschewitz et al. [@roschewitz2025shiftid]: the feature tests are repeated against the weighted reference, using Kish's effective sample size [@kish1965] and Holm correction. A feature that still differs carries a covariate shift. If no feature differs and the predicted labels have moved, the shift is a prior shift. Algorithm @alg:labelfree gives the stage in full.

```Label-free diagnosis {#alg:labelfree}
Input:  calibration part R (with labels and predictions), window W (predictions only), level alpha
Output: verdict in {no shift, covariate, prior}, shifted features
1  p_f ← per-feature tests of W against R (KS or chi-square)
2  p_y ← chi-square test of the predicted labels
3  p_m ← MMD permutation test
4  weights: 1/3 per block, the feature block's third split evenly over features
5  rejected ← weighted Holm(p_f, p_y, p_m, weights, alpha)
6  if nothing is rejected then return no shift
7  w ← BBSE class weights: solve C w = mu
8  p_r ← per-feature tests of W against R weighted by w (Kish sample size)
9  residual ← features rejected by Holm(p_r, alpha)
10 if residual is not empty then return covariate, residual features
11 if the predicted labels moved then return prior
12 return covariate (joint shift seen by MMD only)
```

**Audit stage.** Concept drift and label noise do not touch the inputs or the model outputs, so only labels can reveal them. The audit draws $m$ late labels (here \res{acs-audit-n}) and first checks, with a one-sided two-proportion test, whether accuracy has dropped against the calibration part. If it has, the next question is whether the change in errors depends on a feature. A logistic model of whether a prediction is correct is fitted on the calibration rows and the audit rows together. Its null form holds \res{const-quantile-bins} confidence bins at reference quantiles, bins of a feature $f$, an audit indicator and the interaction of that indicator with the confidence bins. The alternative adds the interaction of the indicator with the bins of $f$. A likelihood ratio test compares the two for each feature, with Holm correction across features.

The confidence term is what separates the two types. In a binary task, uniform label noise at rate $r$ makes the probability of a correct prediction equal to

$$P(\mathrm{correct}\mid x) = r + (1-2r)\,q(x)$$ {#eq:noise}

\noindent where $q(x)$ is the model's own probability of being right at $x$. Under label noise the change in errors therefore depends on $x$ only through $q(x)$, which the confidence bins of the null absorb. Concept drift, by contrast, moves the errors inside a region of some feature, so a feature that stays significant after correction points to concept drift. If no feature is significant, the verdict is label noise, as Eq. (@eq:noise) predicts. Algorithm @alg:audit gives the stage.

```Audit diagnosis {#alg:audit}
Input:  model M, calibration part R with labels, audit sample (X_a, y_a), level alpha
Output: verdict in {no drift, concept, label noise}
1  correct_R, correct_a ← whether M is right on R and on the audit
2  if the one-sided two-proportion test finds no drop in accuracy then
3      return no drift
4  for each feature f do
5      null: logit P(correct) = confidence bins + bins(f) + audit + audit:confidence bins
6      alternative: null + audit:bins(f)
7      p_f ← likelihood ratio test of alternative against null
8  structured ← features rejected by Holm(p_f, alpha)
9  if structured is not empty then return concept, first structured feature
10 return label noise
```

### Root Cause Analysis {#sec:alg-rca}

The drift type suggests what kind of fix to consider but not where the trouble started. Root cause analysis asks which inputs the model now leans on more or less than before. For tabular models we compute Shapley additive explanations (SHAP) [@lundberg2017unified] of the deployed model with its preprocessing on \res{acs-shap-n} rows per side against \res{acs-shap-bg} background rows and compare the mean absolute attribution of every feature on reference and window rows. Each change gets a percentile bootstrap interval, Bonferroni adjusted over the features, so that only clear changes are reported. For image models, class activation maps (CAM) [@zhou2016cam] highlight the image regions behind the prediction of the linear head on the frozen network. Fig. @fig:cam shows examples from the CLEAR-10 stream.

![Class activation maps for the \res{cam-k} images of CLEAR-10 bucket \res{cam-bucket} with the highest out-of-distribution scores. The top row gives each image with its predicted and true class, the bottom row the map of evidence for the predicted class (red is most evidence)](gen_cam.png){#fig:cam width=150}

The images were chosen as the most unusual of the bucket, because unusual images are where a change in content shows first. The model predicts all four correctly and the maps show which regions carry the evidence for each prediction; for the laptop it is the keyboard. Root cause analysis narrows the search for a cause without proving one, which is why its findings are always shown next to the localization and the drift type.

### Reliability Scoring and Remediation Triage {#sec:alg-triage}

The last two stages act on single predictions and on the decision to retrain. Fig. @fig:flow-triage shows both.

![Flowcharts of (a) the reliability score of each prediction and (b) the remediation triage](flow_triage.png){#fig:flow-triage width=150}

For single predictions three signals are combined, each scaled between 0 and 1: the confidence risk $1-c$, the instability of the prediction under small perturbations of the input and an out-of-distribution (OOD) score that blends an Isolation Forest [@liu2008isolation] with a standardized distance. A logistic regression on the calibration part maps the three signals to a probability of error. It is fitted only if the calibration part holds at least ten wrong predictions per signal [@peduzzi1996]; with fewer, the risk falls back to $1-c$.

The triage has to judge, without production labels, whether retraining is worth the trouble. It uses two probes, given in Algorithm @alg:triage. The first relies on density ratio weights from a classifier trained to tell reference rows from window rows; the weights are fitted on separate folds and capped at \res{const-weight-clip} times their mean [@cortes2010weights]. A model retrained with them is compared with an unweighted model on a held-out \res{const-triage-valfrac}% of the reference, weighted in the same way [@shimodaira2000; @sugiyama2007]. The second probe needs late labels from an earlier window. Where they exist, it retrains on them and checks the result on a held-out part of that window.

```Remediation triage {#alg:triage}
Input:  reference data R, window W (unlabeled), optional earlier labeled window E, level alpha
Output: recommend or hold, predicted gains
1  d ← classifier separating R from W, fitted on separate folds
2  w ← density ratio weights from d, capped at \res{const-weight-clip} times their mean
3  hold out \res{const-triage-valfrac}% of R as validation data
4  gain_1 ← weighted accuracy of the weighted retrain minus the deployed model
5  if E exists then
6      gain_2 ← accuracy on held-out E of a retrain on E minus the deployed model
7  p ← bootstrap p values of the gains
8  if some gain is significant after Holm over the probes then recommend
9  else hold
```

## Dataset Sources and Utilization {#sec:datasets}

The real datasets were chosen because the cause of their drift is documented, which lets the verdicts be checked against known events. Table @tab:datasets lists all four and the paragraphs that follow give their source, licence, size, features, preparation and use.

Table: Datasets, drift windows and reference accuracy {#tab:datasets size=9}
<<gen:tab_datasets>>

Rows gives the smallest and the largest window, Inputs the number of features or embedding dimensions and the last two columns the reference test accuracy of LR and GB.

*ACS Income and ACS Employment.* Both tasks come from the American Community Survey (ACS) of the United States Census Bureau, as packaged by Folktables [@ding2021retiring] (code under the MIT licence; data under the Census Bureau's terms of use; accessed through the Folktables package). ACS Income predicts from \res{inc-nfeatures} features whether a person earns more than \$50,000 and ACS Employment predicts from \res{emp-nfeatures} features whether a person aged 16 to 90 is employed. Table @tab:features lists the features of ACS Income. California (CA) 2014 is the reference, with \res{inc-train-n} training rows for ACS Income. The temporal windows are CA 2015 to 2019 and 2021 to 2023, as no standard 2020 release exists [@census2021experimental] and the geographic windows are Texas (TX), New York (NY), Florida (FL) and Washington (WA) in 2014. Missing values are coded as $-1$. In 2019 the relationship variable RELP was replaced by RELSHIPP [@census2019pums], which we map back to RELP with the code labels of the 2018 and 2019 data dictionaries. Five documented changes fall in these years: new occupation codes in 2018 [@census2020occupation], a redesigned relationship question in 2019, a new coding of race answers from 2020 [@census2021race], the pandemic and wage growth against the fixed income threshold.

Table: Input features of ACS Income {#tab:features widths=1.2,3.2,1.5 size=10}
| Code | Description | Type |
|---|---|---|
| AGEP | Age | Numeric |
| COW | Class of worker | Nominal |
| SCHL | Educational attainment (24 ordered levels) | Ordinal, treated as numeric |
| MAR | Marital status | Nominal |
| OCCP | Occupation | Nominal |
| POBP | Place of birth | Nominal |
| RELP | Relationship to the reference person | Nominal |
| WKHP | Usual hours worked per week | Numeric |
| SEX | Sex | Nominal |
| RAC1P | Race | Nominal |

Nominal codes such as occupation are one-hot encoded for LR, split natively by GB and tested with count-based statistics by the detectors, because their numeric order means nothing.

*Gas sensor array drift.* This dataset from the machine learning repository of the University of California, Irvine (UCI) holds 13,910 measurements of six gases by 16 metal oxide sensors, taken over 36 months in ten batches [@vergara2012gas; @rodriguezlujan2014gas], with eight features per sensor (licence CC BY 4.0). As the sensors age, their response to the same gas drifts while the labels stay exact, a documented change in $P(X\mid Y)$. Batches 1 and 2 form the reference and batches 3 to 10 the windows. Some batches are small, so the number of audit labels for a window of $n$ rows is given by $\min(600,\lfloor n/2\rfloor)$.

*CLEAR-10.* This image stream from Flickr has ten object classes and a background class, spread over ten time-ordered buckets of about 3,300 images each [@lin2021clear] (licence CC BY 4.0). Bucket 1 is the reference. Images are mapped to the \res{clear-dim}-dimensional output of the global average pooling layer of a frozen residual network with 18 layers (ResNet-18) trained on ImageNet [@he2016deep] and both models are fitted on these embeddings.

**Injection benchmark.** The type of a real drift is never known for certain, so the diagnosis is graded on drift that we inject ourselves into real census data. The benchmark uses the 2014 data of \res{bench-nstates} states (\res{bench-states}) for both ACS tasks. For each of \res{bench-nseeds} seeds the split, the window and the injection are drawn again, which gives \res{bench-nreps} replicates per configuration. A replicate draws a window of \res{bench-prodsize} rows and a grading holdout of \res{bench-holdsize} rows from the test part and each mechanism is injected into both at three intensities. Table @tab:mechanisms lists the mechanisms of the two designs.

Table: Drift mechanisms of the injection benchmark {#tab:mechanisms widths=1.4,3.4,3.4 size=9.5}
| Type | Design A (partly matches the tests) | Design B (held out from the design) |
|---|---|---|
| Covariate shift | Rescale two numeric features (ACS Income: \res{bench-cov-features-inc}) for a random subset of rows | Selection bias: keep each row with probability $\sigma(\beta s(x))$ for a seeded random score $s$ over all inputs, $\beta\in\{\res{bench-b-betas}\}$ |
| Prior shift | Drop rows of one class until the positive rate rises by \res{bench-prior-steps} | Lower the positive rate by \res{bench-b-prior-steps} |
| Concept drift | Invert the labels of the \res{bench-concept-steps}% of rows with the highest value of one feature (ACS Income: \res{bench-concept-feature-inc}) | Invert the labels in the top \res{bench-b-concept-steps}% of a second random score (an oblique region); for ACS Income also raise the income threshold to \res{bench-b-thresholds} |
| Label noise | Flip a random \res{bench-noise-steps}% of the labels | Flip positive labels to negative at rates of \res{bench-b-noise-steps}% |
| Control | A window without drift in every replicate | None |

In design B the rows of the selection-bias windows stay real and $P(Y\mid X)$ is exactly unchanged, so the mechanism is a pure covariate shift that moves many features a little rather than two features a lot. None of the design B mechanisms shaped any part of the procedure, which is what makes it a fair test of whether the diagnosis carries over to new drift.
