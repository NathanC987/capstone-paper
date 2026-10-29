# Results and Discussion {#ch:results}

This chapter presents what the finished system does and how well it does it. It starts with the dashboard, through which a user meets every module, then defines the measures used to judge the system, lists its inputs and settings, reports the results on the benchmark and on real drift, compares them with existing approaches and draws conclusions. It ends with the sustainability assessment that the department asks for.

## User Interface Screenshots for Respective Modules {#sec:ui}

The dashboard is a Streamlit application with one tab per dataset (ACS census data, CLEAR-10 images, the gas sensor array) and one for the injection benchmark. Each tab tells the story of a study in numbered steps that follow the stages of the pipeline and each step opens with the question it answers and ends with a short note, generated from the results, that says what the data show. The screenshots below were taken from the running dashboard on the ACS Income study with logistic regression unless stated otherwise. Fig. @fig:ui-overview shows the top of the ACS tab.

![Top of the ACS tab: task and model selectors, the description of the study, the headline numbers and the strip of steps](ui_overview.png){#fig:ui-overview width=160}

The user chooses the task (ACS Income or ACS Employment) and the monitored model. The headline numbers summarize the study: the reference accuracy of \res{inc-lr-ref-acc}, the \res{inc-nwindows} production windows, the \res{inc-nsigdrop} windows whose accuracy dropped significantly and the absence of any alarm on the control window. The strip of steps doubles as a table of contents. Fig. @fig:ui-cbpe shows the first analysis step, the label-free accuracy estimate.

![Step 2a: the label-free accuracy estimate (CBPE) against the measured accuracy, its error per window and the confidence histograms of the reference and of CA 2023](ui_cbpe.png){#fig:ui-cbpe width=140}

The left chart shows that the estimate follows the measured accuracy closely at first and then stays too high as the years pass and the bar chart on the right gives the size of that error per window. The confidence histograms below show why: the model's confidence barely moves in CA 2023 even though its accuracy has fallen, which is the failure mode described in Section @sec:alg-estimation. Fig. @fig:ui-detection shows how each detector behaves on the same windows.

![Step 2b: the statistic of every detector per window and, at the bottom, which detector raised an alarm on which window (filled circles)](ui_detection.png){#fig:ui-detection width=110}

Each small chart traces one detector's statistic across the windows and the alarm matrix at the bottom shows at a glance that no detector fires on the held-out control window while most fire from 2016 onwards. The population stability index is the most reluctant detector. Fig. @fig:ui-localization shows where the inputs moved.

![Step 2c: effect size of every feature per window (KS statistic for numeric features, Cramér's V for nominal ones; a star marks a significant shift) and the share of rows with occupation codes never seen in the reference](ui_localization.png){#fig:ui-localization width=145}

The heat maps show that occupation and place of birth carry the largest shifts and the bar chart at the bottom shows the jump in unseen occupation codes from 2018, when the census introduced new codes. Fig. @fig:ui-shap shows what the model now relies on.

![Step 3a: change in the mean absolute SHAP value of each feature per window and the reliance on each feature in the reference and in CA 2023](ui_shap.png){#fig:ui-shap width=140}

The model leans less on occupation in the later windows, consistent with codes it has never seen, while its reliance on the other features changes little. Fig. @fig:ui-diagnosis shows the drift type.

![Step 3b: the decision path of the diagnosis for every window, from the label-free tests to the audit, with the verdict on the right; below, the actual, predicted and BBSE-estimated share of positive cases](ui_diagnosis.png){#fig:ui-diagnosis width=120}

Each row is a window and each column a question of the decision path in Fig. @fig:decision. The control window and CA 2015 pass every label-free test and the audit, so they are called no drift, while every later window is stopped at the label-free stage as covariate shift. The chart below shows the label problem of CA 2023: the actual share of positive cases rises much faster than the model predicts, which no label-free test can see. Fig. @fig:ui-reliability shows the reliability of single predictions.

![Step 4: how well each signal ranks wrong predictions above right ones (area under the ROC curve), the share of predictions per risk label, the error rate inside each label and the weights the fusion learned](ui_reliability.png){#fig:ui-reliability width=115}

The fused score sits on top of confidence alone in every window and the learned weights put almost all the emphasis on confidence. The risk labels are ordered correctly: the high-risk group has the highest error rate. Fig. @fig:ui-remediation shows the remediation step.

![Step 5: accuracy recovered by each repair strategy in each window, graded on labeled data (blue means a gain, red a loss, gray not applicable)](ui_remediation.png){#fig:ui-remediation width=160}

Retraining on the most recent labeled window recovers accuracy in almost every temporal window, while importance weighting helps only in some and dropping drifted features costs accuracy. Fig. @fig:ui-clear shows the image tab.

![CLEAR-10 tab, step 3a: class activation maps of the most unusual images of bucket 10](ui_clear.png){#fig:ui-clear width=160}

For images, root cause analysis shows where the model looks, as described in Section @sec:alg-rca. The benchmark tab grades the diagnosis on injected drift; Fig. @fig:ui-bench-type shows its drift type step.

![Benchmark tab, step 6: injected against diagnosed drift types, the stage at which each verdict was reached, the effect of the audit size and the correct diagnosis by intensity](ui_bench_type.png){#fig:ui-bench-type width=135}

The confusion matrix fills mostly the diagonal, the stage chart shows that covariate and prior shifts are settled without labels while concept drift and label noise need the audit and the intensity chart shows that the hardest cases are the mildest ones. Fig. @fig:ui-bench-baselines compares the procedure with the alternatives.

![Benchmark tab, step 7: share of windows whose drift type is named correctly by our procedure, the rule baselines, the learned meta-classifier and the ablations, with paired tests](ui_bench_baselines.png){#fig:ui-bench-baselines width=145}

The chart and the table of paired tests show the comparison that Section @sec:graphs reports in full.

## Performance Evaluation Measures {#sec:metrics}

Each part of the system is judged by a measure suited to the claim it makes.

- **Correct-type rate.** The share of benchmark windows whose drift type is named correctly, with a 95% Wilson interval [@wilson1927]. It is the main measure of the diagnosis because a wrong type leads to a wrong response.
- **False alarm rate.** The share of control windows (no drift) on which a detector raises an alarm or the diagnosis names a drift type. It checks the error rates the design promises: at most α for each detector and 2α for the diagnosis.
- **Paired comparison.** Each method is compared with ours through the per-replicate difference in the correct-type rate, tested by a sign-flip permutation test with \res{bench-nflips} flips and Holm correction. Replicates are the unit of analysis because the windows of one replicate share a model and a reference.
- **Mean absolute error of accuracy estimates.** The average absolute difference, in percentage points, between an estimated and a measured accuracy.
- **Area under the ROC curve (AUROC).** How well a risk score ranks wrong predictions above right ones; 0.5 is chance and 1 is perfect.
- **Triage accuracy and recall.** The share of settings in which the triage's advice matches whether a retrain truly helped and the share of truly helpful retrains it recommends.
- **Run time.** Seconds per window through the stages of the pipeline, excluding model training and image embedding.

## Input Parameters / Features Considered {#sec:params}

The inputs of each study are the features of its dataset (Table @tab:features for ACS Income; \res{emp-nfeatures} features for ACS Employment, 128 sensor features for the gas array and \res{clear-dim} embedding dimensions for CLEAR-10) and the model's predictions and class probabilities. Table @tab:params lists the settings that control the tests, all fixed before the evaluation.

Table: Settings of the pipeline and the benchmark {#tab:params widths=3.2,1.6,3.6 size=9.5}
| Setting | Value | Rationale |
|---|---|---|
| Significance level α | \res{acs-alpha} | Conventional level; fixes the false alarm rate |
| Reference split (train / calibration / test) | \res{acs-split-pct-train} / \res{acs-split-pct-calibration} / \res{acs-split-pct-test}% | Disjoint parts for fitting, reference windows and control |
| PSI alarm threshold | \res{acs-psi-threshold} | Conventional value [@siddiqi2006] |
| MMD permutations | \res{acs-mmd-perm} | Enough for p values well below α at modest cost |
| Minimum expected count per chi-square cell | \res{const-min-expected} | Standard rule for the chi-square approximation [@cochran1954] |
| Audit labels per window | \res{acs-audit-n} | Where more labels stop paying off (Fig. @fig:budget) |
| Confidence bins in the audit null | \res{const-quantile-bins} | Absorb the confidence-driven part of error changes |
| Domain classifier rows per side | \res{acs-dc-n} | Balanced classifier test |
| SHAP rows per side / background rows | \res{acs-shap-n} / \res{acs-shap-bg} | Stable attributions at bounded cost |
| Importance weight cap | \res{const-weight-clip} × mean | Limits the variance of weighted estimates |
| Triage validation share | \res{const-triage-valfrac}% | Held-out reference for the weighted comparison |
| Benchmark states / seeds / replicates | \res{bench-nstates} / \res{bench-nseeds} / \res{bench-nreps} | Variation across populations and draws |
| Benchmark window / holdout rows | \res{bench-prodsize} / \res{bench-holdsize} | Realistic window size; labeled grading data |

## Graphical and Statistical Output {#sec:graphs}

The results are presented in the order of the questions they answer: how often the drift type is named, whether that carries over to new drift, how many labels the audit needs, how well the building blocks work, how the system behaves on real drift, what the last two stages achieve and how long it all takes.

### Drift Type against Baselines

The most direct test of the diagnosis is how often it names the injected type, compared with the alternatives. Table @tab:methods gives this share for every configuration, each with \res{bench-nreps} replicates.

Table: Share of benchmark windows with the correct drift type (%) {#tab:methods size=8.5}
<<gen:tab_methods>>

Inc. and Emp. stand for ACS Income and ACS Employment and A and B are the two benchmark designs. An arrow marks a method that differs significantly from ours after Holm correction: a down arrow means that ours is better and an up arrow that ours is worse. The upper block lists the competing methods and the lower block the ablations of our procedure.

With LR on ACS Income, our procedure names the type in \res{b-inc-a-lr-ours-acc}% of design A windows (95% interval \res{b-inc-a-lr-ours-ci}), while the best rule baseline reaches \res{b-inc-a-lr-errorratemonitoring-acc}%. The rules are held back by design, since each can name only some of the five outcomes. Over all eight configurations our procedure is significantly better in \res{bench-nbetter} of the \res{bench-ntests} comparisons with a baseline or the learned rule and significantly worse in \res{bench-nworse}, \res{bench-worse-cells}.

On design A the learned meta-classifier is the strongest competitor. Validated on states it has not seen, it reaches \res{b-inc-a-lr-metaclassifier-acc}% on ACS Income, above our \res{b-inc-a-lr-ours-acc}%. The held-out mechanisms of design B turn this around. Trained on design A, the meta-classifier drops to \res{b-inc-b-lr-metaclassifier-acc}% on ACS Income and \res{b-emp-b-lr-metaclassifier-acc}% on ACS Employment, while our procedure keeps \res{b-inc-b-lr-ours-acc}% and \res{b-emp-b-lr-ours-acc}%. The learned rule had tied each type to the size and shape of the injected shift; it had learned, for example, that covariate shift means a large shift in two features and so it missed selection bias, which moves many features a little. This is the main argument for tests over a learned rule: the tests encode what the drift types are, not what the training examples happened to look like. Fig. @fig:confusion breaks the results down by type for LR.

![Injected (rows) and diagnosed (columns) drift types on the benchmark with LR, in counts of windows; darker cells hold a larger share of their row](confusion.png){#fig:confusion width=110}

A perfect diagnosis would fill only the diagonal. Design B has no control windows, so false alarms are measured on design A, where most errors sit in the label noise row: noise is read either as concept drift or as no drift. Our procedure raised a false alarm on \res{diag-fa-n} of \res{det-ncontrols} control windows (\res{diag-fa-pct}%, 95% CI \res{diag-fa-ci}), \res{diag-fa-labelfree-n} in the label-free stage and \res{diag-fa-audit-n} in the audit, below the bound of \res{diag-fa-bound-pct}%.

The ablations show which parts of the procedure carry the weight. Without the confidence term in the audit null, accuracy on ACS Income design A falls by \res{b-inc-a-lr-noconfidencenull-diffabs} points, because uniform label noise then looks like concept drift. Dropping the MMD block changes little on the benchmark (\res{b-inc-a-lr-nommd-diff} points), whose shifts are visible feature by feature; its value shows on the image embeddings of CLEAR-10. Replacing the confidence bins by cells of predicted class and confidence helps on ACS Employment design B (\res{b-emp-b-lr-classconfidencenull-acc}% against \res{b-emp-b-lr-ours-acc}%) but costs accuracy on ACS Income design A (\res{b-inc-a-lr-classconfidencenull-acc}%). Switching to it after seeing design B would bias the comparison, so it stays an ablation and a direction for future work.

### Held-out Mechanisms

Design B asks whether the procedure carries over to drift it was not built for. Table @tab:mech-results gives the result per mechanism.

Table: Correct-type rate (Corr., %) and mean accuracy drop (Drop, points) per held-out mechanism of design B {#tab:mech-results size=9}
<<gen:tab_mechanisms>>

Three of the five mechanisms carry over well. Selection bias is named covariate shift in \res{b-inc-lr-mech-selection-id}% of ACS Income windows with LR, even though no value is distorted and the shift is spread across all features. A lower positive rate is named prior shift in \res{b-inc-lr-mech-priordecrease-id}% and concept drift in an oblique region, which no single feature bounds, is still recognized in \res{b-inc-lr-mech-conceptoblique-id}%.

The other two are harder. A higher income threshold relabels some rows, yet model accuracy hardly moves (mean drop \res{b-inc-lr-mech-conceptthreshold-drop} points), so the audit stops at its first question and reports no drift in \res{b-inc-lr-mech-conceptthreshold-as-none} of the \res{b-inc-lr-mech-conceptthreshold-n} windows. This is intended: the procedure looks for drift that costs accuracy and this drift costs almost none. Class-conditional label noise is recognized in only \res{b-inc-lr-mech-classnoise-id}% of ACS Income windows. At low flip rates the loss is too small to show in \res{bench-audit-n} labels and at high rates the errors follow the true class, which is itself correlated with the features, so the error-structure test reads the pattern as concept drift. A null model built on confidence alone cannot separate the two, a true limitation of the method.

### Size of the Delayed Audit

Labels cost money, so it matters how many the audit needs. We varied the audit size on ACS Income design A with LR. Fig. @fig:budget shows the result.

![Share of concept drift and label noise windows identified correctly at audit sizes of \res{bench-audit-sizes} labels (ACS Income, design A, LR), with 95% intervals](audit_budget.png){#fig:budget width=110}

With 200 labels concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows and label noise in \res{b-inc-a-lr-budget-labelnoise-200}%. With 600 labels the two rates reach \res{b-inc-a-lr-budget-concept-600}% and \res{b-inc-a-lr-budget-labelnoise-600}% and going on to 1,000 labels adds little (\res{b-inc-a-lr-budget-concept-1000}% and \res{b-inc-a-lr-budget-labelnoise-1000}%). The \res{acs-audit-n} labels used throughout therefore sit where more labels stop paying off.

### Detection and Accuracy Estimation

The diagnosis rests on the detectors and on the accuracy estimate, so both were checked on the benchmark. Table @tab:detectors gives the alarm rate of every detector by injected type.

Table: Alarm rate of each detector by injected type on design A (%), with the 95% interval on the control windows {#tab:detectors size=9.5}
<<gen:tab_detectors>>

On the \res{det-ncontrols} control windows the 95% interval of every detector's false alarm rate contains α = \res{acs-alpha} or lies below it. All detectors catch covariate shift and all except PSI catch most prior shifts. In concept drift and label noise windows the inputs are the same as in the control window of their replicate, so no detector can see them; their alarm rates equal the control rates. This is why the audit is needed. Table @tab:estimators compares the four accuracy estimates.

Table: Mean absolute error of the four accuracy estimates (percentage points); the best value in each column is in bold {#tab:estimators size=9.5}
<<gen:tab_estimators>>

On design A all four estimates stay within \res{est-bench-none-max} points without drift and within \res{est-bench-covariate-max} points under covariate shift. Under concept drift and label noise every error equals the whole loss, about \res{est-bench-conceptnoise-cbpe} points, because the inputs do not change. Across the \res{est-ncols} columns ATC has the smallest error in \res{est-nbest-atc} and CBPE in \res{est-nbest-cbpe}. On the gas sensor data all four miss by \res{est-gas-best} to \res{est-gas-worst} points on average: in batch 8 the mean confidence of the LR model falls from \res{gas-ref-conf} to \res{gas-b8-conf} and its accuracy to \res{gas-b8-acc}, yet CBPE estimates \res{gas-b8-est}. The estimate is best read as an upper bound on accuracy.

### Real Drift {#sec:real}

On real data the type of drift is not known, but its causes are on record. The question is whether the verdicts agree with those causes and whether the control windows stay quiet. Fig. @fig:timelines shows how accuracy changes over time in all four datasets.

![Measured accuracy of both models and the label-free CBPE estimate on the temporal windows of the four datasets](gen_timelines.png){#fig:timelines width=160}

C marks the control window and the numbers mark years (ACS), batches (gas sensor) or buckets (CLEAR-10). The gap in the ACS lines is the missing 2020 release. Across the four datasets no real window was named prior shift, concept drift or label noise. Most of the documented causes act on the inputs, from new codes and a redesigned question to aging sensors, so covariate verdicts are what one would expect. Table @tab:income gives the details for ACS Income, which shows the clearest trend.

Table: Detection and diagnosis on the ACS Income windows. The alarms are those of the LR model; Conf. is the confidence test and DC the domain classifier {#tab:income size=8}
<<gen:tab_income>>

Δ is the change in accuracy, in points, against each model's accuracy on the control window and Est. err. is the error of the CBPE estimate. A tick marks an alarm and Type is the verdict of the diagnosis, the same for LR and GB in every window. Top shifts lists the two features with the largest effect size.

Accuracy falls over time for both models, with LR going from \res{inc-ca2015-acc} in 2015 to \res{inc-ca2023-acc} in 2023, while the CBPE estimate falls far less. Neither model raises an alarm on the control window; both call CA 2015, whose accuracy did not change significantly, no drift and every other window covariate shift. The documented events can be read off the localization. The 2018 revision of the occupation codes left \res{inc-ca2018-unseen-occp}% of rows with a code that never occurred in 2014 and occupation lost weight in the model as a result (SHAP change \res{inc-ca2018-shap-occp}). Relationship moves in 2019 (effect size \res{inc-ca2019-eff-relp}), when its survey question was redesigned and race moves from 2021 (effect size \res{inc-ca2021-eff-rac1p}), once the Census Bureau had changed its coding of written race answers [@census2021race]. Wage growth against a fixed income threshold shows up in the labels instead: their positive share rises from \res{inc-ctrl-posrate} in the control window to \res{inc-ca2023-posrate} in 2023 while the model predicts only \res{inc-ca2023-predposrate}. Part of the 2023 loss therefore comes from a change in what the labels mean, which no label-free test can detect.

The cost of a drift differs widely between datasets. On ACS Employment every window is diagnosed as covariate shift, yet LR accuracy never changes by more than \res{emp-dacc-maxabs} points; an alarm alone would overstate the problem and the accuracy estimate keeps it in proportion. The gas sensor batches all come out as covariate shift, as they should for aging sensors that alter $P(X\mid Y)$, with the largest loss in batch 8 (\res{gas-b8-dacc} points for LR). BBSE at first takes each gas batch for a prior shift, since the predicted labels move too, but the consistency test corrects this: the sensors respond differently to a gas mix that has not changed. CLEAR-10 drifts more gently. Buckets \res{clr-windownums-none} show no drift for either model and buckets \res{clr-windownums-covariate} show covariate shift. In buckets \res{clr-windownums-mmdonly} no single embedding dimension shifts significantly with LR; only the MMD test sees the change, which is why the multivariate block is needed. The only detector alarm on any control window comes from the domain classifier baseline on CLEAR-10 ($p=\res{clr-ctrl-dc-p}$), a false alarm of the kind that α allows.

### Reliability and Triage

The fused risk score is judged by how well it ranks wrong predictions above right ones. Where the fusion is learned, on ACS and CLEAR-10, its AUROC differs from that of confidence alone by \res{rel-other-diff-min} to \res{rel-other-diff-max} over \res{rel-other-n} windows and by \res{rel-bench-gain-min} to \res{rel-bench-gain-max} on the benchmark. On the gas sensor array the calibration part holds too few wrong predictions (\res{rel-gas-lr-cal-errors} with LR and \res{rel-gas-hgb-cal-errors} with GB), so the risk falls back to confidence. Confidence alone carries most of the information about a single prediction; the other signals add almost nothing, an honest negative result.

For the triage, a retrain truly helps when importance weighting or the latest labeled window raises holdout accuracy significantly. Table @tab:remediation gives the outcome per setting.

Table: Remediation by setting: settings with a significant gain from importance weighting (IW), retraining on the recent window and retraining on fresh labels and the triage's advice {#tab:remediation size=9}
<<gen:tab_remediation>>

Over \res{rem-n} real settings the triage is right in \res{rem-triage-correct}. It is right in \res{rem-recent-correct} of the \res{rem-recent-n} settings that have an earlier labeled window, because its recent-window probe is checked on real labels. The geographic windows of the census tasks have no earlier window; there, importance weighting rarely helps and the triage is right in \res{rem-norecent-correct} of \res{rem-norecent-n} settings, but mostly by advising against a retrain, since one truly helped in only \res{rem-norecent-helps} of them. On the benchmark its recall is only \res{b-inc-a-lr-triage-recall}%, because importance-weighted validation cannot see gains outside the reference data.

### Computational Cost {#sec:cost}

A monitor has to finish with one window before the next one arrives, so the time of each window was recorded through the stages of the pipeline, from the detectors to the reliability scores, leaving out model training and the image embeddings. Over \res{bb-nwindows-timed} real windows no window took longer than \res{bb-time-max} seconds and all of them together took \res{bb-time-total-min} minutes. With LR on the census tasks most of the time goes to the SHAP values of the root cause analysis; on CLEAR-10 and the gas sensor array the diagnosis takes the largest share. The whole injection benchmark took \res{bench-total-hours} hours on \res{const-cpu-cores} processor threads. Windows of a day, a week or a month leave ample room; a stream that needs a verdict every few seconds would call for cheaper tests.

## Comparison of Results with Existing Systems {#sec:compare-results}

The comparison in Table @tab:methods is fair in three respects. Every method names one of the same five outcomes, from the same tests and the same audit labels, so differences come from how the evidence is turned into a verdict, not from different data. The rule baselines stand for current practice: input monitoring reads any input alarm as covariate shift, BBSE first reads a shift in the predicted labels as prior shift [@lipton2018bbse; @rabanser2019failing] and error-rate monitoring also reads a drop in audit accuracy as concept drift [@gama2004ddm]. The learned meta-classifier, a GB model trained on nine statistics of each window from the same tests, checks whether a learned rule could replace the tests.

Against the rules, our procedure is better in every configuration, by a wide margin, because each rule can name only some of the types. Against the learned rule, the picture depends on whether the drift was seen in training: the meta-classifier wins narrowly on design A and loses by a wide margin on every configuration of design B. A monitoring team does not know in advance which drift it will meet, so a procedure that holds up on unseen mechanisms is the safer choice. Compared with the published methods of Table @tab:positioning, the system is the only one that separates concept drift from label noise and the only one evaluated on held-out drift. Its accuracy estimates are on par with the best published estimators: ATC is slightly more accurate in most columns of Table @tab:estimators and all four fail together when confidence stops tracking accuracy.

## Inference Drawn {#sec:results-inference}

The results support four conclusions. First, hypothesis tests with a stated error rate can name the drift type from label-free tests and a few hundred late labels: \res{bench-a-ours-min} to \res{bench-a-ours-max}% on design A and \res{bench-b-ours-min} to \res{bench-b-ours-max}% on held-out drift, with false alarms below their bound. The project's objectives for the diagnosis were met. Second, encoding the definitions of the types makes the diagnosis carry over to new drift, where a learned rule does not. Third, on real data the system stays quiet on control windows and traces documented events, from new occupation codes to aging sensors, while showing that an alarm alone can overstate a harmless shift. Fourth, the supporting stages have clear limits: the accuracy estimate is an upper bound, the reliability fusion adds little beyond confidence and the triage is reliable only where an earlier labeled window exists.

Two results were unexpected. The first was how strongly the meta-classifier collapsed on design B, which made the case for tests clearer than we had anticipated. The second was class-conditional label noise, which the audit mostly reads as concept drift; this exposed a real limit of a confidence-based null and points to the main next step of the work.

## Sustainability Impact Assessment and Rubric Justification {#sec:sustain}

This section assesses the sustainability of the project with the structure the department provides: its scope and evidence, the material topics, targets and progress, the link to the Sustainable Development Goals, a self-assessment against the rubric and a statement of limitations. It distinguishes throughout between what was measured, what was estimated and what was not assessed.

### Scope, Boundary and Evidence

The assessment covers the development and evaluation of ResilientAI from February to October 2026: the experiments on the team's workstation, the dashboard and the documents. Hosting, use by a real monitoring team, maintenance and disposal are outside the boundary, because the system has not been deployed. The users considered are the stakeholders of Section @sec:req-intro. The evidence consists of the measured run times stored in every study report, the benchmark's recorded wall-clock time, the processor's rated maximum power of 181 W [@intel14600k], the average emission factor of the Indian grid of 0.727 kg of carbon dioxide per kWh for 2023–24 [@cea2024co2] and the design documents of the system. There is no earlier version of the system to serve as a baseline, so comparisons are made against the alternative a team would otherwise use, such as labeling every window.

### Material Sustainability Topics

Table @tab:material lists the environmental, social and governance topics, their relevance to this project and the evidence for each.

Table: Material sustainability topics {#tab:material widths=1.6,2.5,1.7,1.6,1.6 size=8.5}
| Dimension / topic | Project relevance and potential impact | Indicator / unit | Evidence source | Boundary / limitation |
|---|---|---|---|---|
| Environment: energy / compute | Material: experiments and monitoring use electricity; the triage can avoid needless retraining | kWh; seconds per window | Stored run times; rated power | Upper-bound estimate; not metered; development time excluded |
| Environment: emissions / travel | Material through electricity use; no travel was needed beyond normal college attendance | kg CO₂ | Energy × grid factor | Grid average, not marginal factor |
| Environment: materials / waste | Not material: no hardware was bought or discarded | – | Budget (Table @tab:budget) | Existing workstation's life cycle not assessed |
| Social: access / inclusion / usability | Monitoring teams of any size can run the system on ordinary hardware; dashboard explains each step in plain language | Steps with a question and a generated note | Dashboard (Section @sec:ui) | No study with outside users |
| Social: safety / well-being / community | Catching a failing model early protects the people its decisions affect | False alarm rate; correct-type rate | Section @sec:graphs | Indirect; no deployment |
| Governance: privacy / security / fairness | Public data only, local processing; census tasks include sensitive attributes | Personal records collected; data leaving the machine | Design; dataset licences | No fairness audit of the monitored models |

### Sustainability Targets and Progress

Table @tab:targets sets project-specific targets for the material topics. They were set for this assessment from the requirements of Chapter @ch:req; where no baseline exists, the alternative a team would otherwise use serves as the reference.

Table: Sustainability targets and progress {#tab:targets widths=2.2,2.0,1.6,1.8,1.6 size=9}
| Topic / target | Baseline and date | Target / due date | Actual result | Status / corrective action |
|---|---|---|---|---|
| Labels needed per window | Label the whole window: \res{bench-prodsize} rows (benchmark) | At most \res{acs-audit-n}, by October 2026 | \res{acs-audit-n} audit labels, only when no label-free test rejects | Met |
| Retrain only when it helps | Retrain on every alarm | Triage right in most settings, by October 2026 | Right in \res{rem-triage-correct} of \res{rem-n} real settings | Met with real labels; low recall without them; future work |
| Compute per window | None | Within a daily cycle on one workstation | At most \res{bb-time-max} s per window | Met |
| Energy of all experiments | None | Below 5 kWh | About \res{bb-energy-total-kwh} kWh (upper bound) | Met; meter future runs |
| Personal data collected | None | Zero records | Zero | Met |
| Plain-language explanation | None | Every dashboard step | Every step has a question and a generated note | Met; no accessibility audit yet |

### SDG Alignment and Evidence

The links of Section @sec:sdg can now be graded. For SDG 9, target 9.5, the link is a tested output: the audit test and the error-controlled diagnosis were built and evaluated with the results above and then described in a research paper. For target 9.4 it is an expected contribution: the system keeps deployed models reliable in evaluation, but it has not yet been used in a real deployment. For SDG 12, target 12.2, the label economy is a tested output (\res{acs-audit-n} labels instead of whole windows), while the computation saved by the triage is a design intent supported by its accuracy on real settings but not measured in a deployment. For target 12.6 the link is demonstrated by this section, which reports energy, emissions, privacy and inclusion with its method and limits. We do not claim any measurable effect on national or global progress towards these goals; the project is a small contribution to their targets.

### Sustainability Assessment Rubric

The department's rubric rates six criteria from 0 to 3. Table @tab:rubric reproduces it and Table @tab:rubric-score gives our self-assessment, to be confirmed by the mentor and examiners.

Table: Sustainability assessment rubric of the department {#tab:rubric widths=1.7,0.8,1.6,1.7,1.9,2.4 size=8}
| Criterion | Weight | 0 – Not evidenced | 1 – Initial | 2 – Developing | 3 – Strong |
|---|---|---|---|---|---|
| A. Scope, materiality and baseline | 15% | No boundary or relevant topics identified | Boundary/topics stated but vague; no baseline rationale | Boundary and material topics explained; baseline partly defined | Clear life-cycle boundary, justified material topics, reporting period and baseline/data gaps stated |
| B. Environmental/resource impacts | 20% | No relevant impact considered | Mentions impacts without method or evidence | Uses relevant indicator(s) with method and some evidence | Quantifies/estimates relevant energy, emissions, materials/waste or explains N/A with sound rationale; method and limits disclosed |
| C. Social value, inclusion and safety | 20% | No social effects considered | Benefits asserted without stakeholder evidence | Stakeholders and relevant usability/accessibility/safety measures identified | Impact on affected users assessed with suitable tests/feedback; inclusion, safety and limitations documented |
| D. Governance, privacy, security and ethics | 20% | Risks not considered | Generic statements only | Relevant risks and controls documented; some verification | Data handling, consent/licensing, security, fairness/accountability controls and test evidence clearly documented |
| E. SDG linkage and measurable targets | 10% | No SDG/target linkage | SDGs listed without causal explanation | Relevant SDG target and plausible indicator linked to project | Target-level mapping, baseline/target/indicator and supporting evidence; expected vs demonstrated impact distinguished |
| F. Measurement, transparency and improvement | 15% | No results or limitations | Anecdotal results; no method or limitations | Metrics/methods/results partly reproducible; limitations noted | Evidence traceable and repeatable; assumptions, uncertainty, gaps and corrective/future actions disclosed |

Table: Self-assessment against the rubric. Weighted points = (rating ÷ 3) × weight {#tab:rubric-score widths=2.4,0.9,0.9,1.1,4.0 size=9}
| Criterion | Weight | Rating | Points | Basis |
|---|---|---|---|---|
| A. Scope, materiality and baseline | 15 | 2 | 10.0 | Boundary, period and material topics stated; no measured baseline, only the alternative practice |
| B. Environmental/resource impacts | 20 | 2 | 13.3 | Energy and emissions estimated with a stated method and sources; not metered |
| C. Social value, inclusion and safety | 20 | 2 | 13.3 | Stakeholders and usability measures identified; no test with outside users |
| D. Governance, privacy, security and ethics | 20 | 2 | 13.3 | Licences, privacy and local processing documented; no fairness audit |
| E. SDG linkage and measurable targets | 10 | 2 | 6.7 | Target-level mapping with indicators; expected and demonstrated effects distinguished; few numeric baselines |
| F. Measurement, transparency and improvement | 15 | 3 | 15.0 | Every number generated from stored outputs and repeatable with seeds; assumptions and gaps disclosed |
| Total | 100 | | 71.7 | Satisfactory (60–79) on the department's suggested scale |

The strongest criterion is transparency, because every figure in the assessment can be traced to stored outputs and rebuilt. The weakest are the social and governance criteria, where the evidence stops at identification: a usability study with outside users and a fairness audit of the monitored models would raise both.

### Evidence and Limitations Statement

The run times and the benchmark's wall-clock time were measured and are stored in the study reports. The energy and emission figures are estimated: they multiply measured time by the processor's rated maximum power, which overstates the real draw and by the average emission factor of the Indian grid for 2023–24 (later versions of the database give lower factors, so this also errs on the high side). They exclude the graphics card's work on image embeddings, the development time and the time spent writing. Inclusion and usability were assessed qualitatively by the team and in mentor reviews. Fairness and accessibility were not assessed. The savings in labels are tested on the benchmark; the savings in computation from the triage are not measured in a deployment. Future work should meter the energy of a full run, run a short usability study with a monitoring team and add a fairness check of the monitored models.
