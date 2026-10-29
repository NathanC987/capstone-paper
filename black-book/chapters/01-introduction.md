# Introduction {#ch:intro}

This chapter introduces the problem that ResilientAI addresses: deployed machine learning models that lose accuracy silently when their data change. It explains why the problem matters, defines it precisely, reviews the systems that exist today and their gaps and ends with the relevance of the project and its link to the United Nations Sustainable Development Goals.

## Introduction {#sec:intro-intro}

A machine learning model is built from a fixed set of historical examples and then put to work on new data, often for a long time. A credit model, a demand forecast or a medical triage tool is trained once, checked on held-out data and deployed. The world it was trained on does not stand still, however. Customers change, sensors age, survey questions are rewritten and occupations are reclassified. The data that reach the model in production drift away from the data it learned from and its predictions get worse. This is known as dataset shift or data drift [@moreno2012unifying; @quionero2009dataset].

The difficulty is that the loss is silent. A deployed classifier keeps producing confident predictions after its accuracy has fallen and the true labels that would expose the loss tend to arrive weeks or months later, if at all [@rabanser2019failing]. Monitoring therefore has to work from what is available at prediction time: the inputs, the model's outputs and its confidence. Model monitoring has become a recognised part of machine learning operations for this reason [@sculley2015hidden; @paleyes2022challenges; @huyen2022designing].

Not every drift is the same. The right response depends on its kind. Moreno-Torres et al. [@moreno2012unifying] distinguish three types of dataset shift and this project adds a fourth. Fig. @fig:drift-types shows the four on a small two-dimensional example.

![The four drift types on toy data with two classes (circles and triangles). The dashed line is the decision boundary learned on the reference data; in (d) the labels are reversed inside the shaded region](drift_types.png){#fig:drift-types width=160}

Panel (a) is the reference data the model was trained on. Under covariate shift (b) the inputs move but the rule that maps inputs to labels holds, so reweighting the training data is often enough to adapt the model. Under prior shift (c) only the class balance changes, which recalibration usually fixes. Concept drift (d) alters the mapping itself: the same inputs now carry different labels in some region and nothing short of fresh labels will repair the model. Label noise (e) is different again. The true relationship is unchanged, but the labels used to grade the model are corrupted, so the fault lies in how labels are collected rather than in the model.

ResilientAI is a monitoring system built around this idea. It takes a deployed model, its labeled training data and a stream of unlabeled production data and for every production window it answers the questions a monitoring team asks in turn. Has the data changed? How much accuracy has been lost? Which features moved? What type of drift is it and what probably caused it? Which predictions should not be trusted? Would a cheap retrain recover the loss? The implementation, its dashboard and the research paper written from this project call the pipeline Data Drift Autopsy; ResilientAI is the name of the project as a whole.

The rest of this report follows the template of the department. Chapter @ch:lit surveys the literature and patents, Chapter @ch:req gathers the requirements and Chapter @ch:design presents the design. Chapters @ch:impl and @ch:testing cover the implementation and its testing, Chapter @ch:results presents the results and Chapter @ch:conclusion concludes.

## Motivation {#sec:motivation}

The motivation for this project came from a simple observation made while working with census data. A model that predicts whether a person earns more than \$50,000, trained on 2014 data from California, loses accuracy year after year when it is applied to later years. The monitoring tools we tried raised alarms on almost every later year, which was correct, yet none of them could say whether the cause was a change in the population, a change in the survey or a change in what the label means. A team receiving such an alarm still has to work out by hand what to do.

There are three practical reasons to want more than an alarm. First, labels are expensive: a team should not have to label every production row to find out whether its model still works. Second, the wrong response wastes effort. Retraining on fresh labels does not help when the labels themselves are noisy and reweighting does not help when the concept has changed. Third, alarms without a stated error rate cannot be trusted. A monitor that tests dozens of features at a fixed threshold will raise false alarms by chance and teams quickly learn to ignore it.

There was also a research motivation. The literature offers good tools for detecting a shift and for estimating accuracy without labels, but, as Chapter @ch:lit shows, no published method separates concept drift from label noise with a small label budget and type diagnoses are rarely tested on drift they were not designed for. Closing that gap with tools a monitoring team can actually run seemed both useful and achievable within a capstone project.

## Problem Definition {#sec:problem}

The project addresses the following problem. Given a deployed classifier, the labeled reference data it was built from and a sequence of unlabeled production windows, the system must decide for each window whether the data have drifted. When they have, it must estimate the accuracy the model is likely to have, locate the features that moved and name the drift type as one of covariate shift, prior shift, concept drift or label noise, so that the matching response can be chosen. Production labels may be used only in a small optional audit of a few hundred rows that arrive late. Every decision must come with a stated error rate, so that a window without drift receives a false verdict with a probability fixed in advance.

The target users are machine learning engineers and monitoring teams who own deployed models and the teams that label data for them. The scope covers tabular classifiers and image classifiers whose images are first mapped to embeddings by a pretrained network. Text models, deep models trained end to end on the production stream and real-time streaming at sub-second latency are outside the scope.

The intended outcome is a working system, evaluated on data where the true drift type is known and on real data whose changes are documented, together with a dashboard that presents the findings to a person who must act on them.

## Existing Systems {#sec:existing}

Several kinds of system already watch deployed models. They differ in what they look at and in what they report.

- **Error-rate monitors** such as the drift detection method (DDM) [@gama2004ddm] and ADWIN [@bifet2007learning] track the error rate of the model and raise an alarm when it rises. They need the true label of every prediction soon after it is made.
- **Label-free shift detectors** compare the production inputs or the model's outputs with the reference data through two-sample tests: univariate tests, kernel tests such as the maximum mean discrepancy [@gretton2012kernel], classifier tests [@lopezpaz2017c2st] and black-box shift detection on the model's outputs [@rabanser2019failing].
- **Label shift estimators** such as black-box shift estimation [@lipton2018bbse] estimate how the class balance has changed, assuming that each class keeps its own input distribution.
- **Performance estimators** such as confidence-based performance estimation [@kivimaki2025performance; @nannyml2023cbpe] estimate the accuracy of the model from its confidence.
- **Monitoring libraries and platforms** package such tests with dashboards, explanations and alerts [@klaise2020monitoring]. Several companies have also patented drift monitoring methods, which Chapter @ch:lit reviews.

## Lacunae in Existing Systems {#sec:lacunae}

The existing systems leave several gaps, each supported by the survey in Chapter @ch:lit.

1. **They detect but do not diagnose.** Label-free detectors report that a shift happened, not what type it was [@rabanser2019failing]. Error-rate monitors notice concept drift but cannot tell it apart from label noise, because both raise the error rate [@gama2004ddm].
2. **Diagnosis needs labeled production data.** The most complete type diagnosis, DetectShift [@maiapolo2023detectshift], tests each part of the joint distribution of inputs and labels but needs labels for the new data, which its authors acknowledge as a limitation.
3. **Label noise is not treated as a drift type.** None of the methods we found separates concept drift from label noise using a small audit of late labels.
4. **Error rates are not controlled across decisions.** Monitors that test many features and several detectors at a fixed threshold do not control the chance of at least one false alarm across all of them.
5. **Methods are graded on their own benchmarks.** Injected drift gives a ground truth but may favor the method being tested. Type diagnoses are rarely checked on drift mechanisms held out from their design.
6. **Accuracy estimates assume that confidence stays honest.** Confidence-based estimates assume that the link between confidence and accuracy survives the shift, which often fails [@ovadia2019trust].

## Relevance of the Project {#sec:relevance}

The project is relevant wherever a model keeps running after its training data have aged. Banks, insurers, public agencies, hospitals and manufacturers all deploy classifiers on populations and processes that change. For them, knowing the type of a drift turns an alarm into an action: reweight, recalibrate, collect fresh labels or check the labeling process. Because the system needs labels only for a small audit, it also lowers the cost of monitoring for teams that cannot label their production data.

The beneficiaries are, first, machine learning engineers and monitoring teams, who get a ranked and explained diagnosis instead of a bare alarm. The people affected by model decisions benefit indirectly when a failing model is caught and repaired sooner. The project also adds to research on dataset shift: its audit test, its error-controlled procedure and its held-out benchmark are described in a research paper prepared for publication (Appendix I).

## Alignment with the United Nations Sustainable Development Goals (SDGs) {#sec:sdg}

The project is linked to two of the seventeen Sustainable Development Goals of the United Nations: Goal 9 (Industry, Innovation and Infrastructure) and Goal 12 (Responsible Consumption and Production) [@un2015agenda]. Table @tab:sdg ties each goal to a specific target, to the part of the project that serves it and to the evidence in this report. The last column states whether each link is a design intent, a tested output or an expected contribution, as the template asks.

Table: Alignment of the project with the Sustainable Development Goals {#tab:sdg widths=1.6,1.9,2.2,2.6,2.3 size=9.5}
| SDG and name | Target | Project component | Contribution | Indicator and evidence |
|---|---|---|---|---|
| SDG 9: Industry, Innovation and Infrastructure | 9.5: enhance scientific research and upgrade technological capabilities | Audit test for concept drift against label noise; error-controlled diagnosis; held-out benchmark | New method and open evaluation design for a monitoring problem without a published solution (tested output) | Correct-type rates in Section @sec:graphs; research paper in Appendix I |
| SDG 9: Industry, Innovation and Infrastructure | 9.4: upgrade infrastructure for greater reliability and efficiency | End-to-end monitoring of deployed models with a stated false alarm rate | Silent model failure is caught and explained instead of going unnoticed (expected contribution) | No false alarm on any real control window; false alarm rate on benchmark controls in Section @sec:graphs |
| SDG 12: Responsible Consumption and Production | 12.2: efficient use of natural resources | Remediation triage, label-free decisions, frozen image embeddings, capped parallel workers | Avoids needless full retraining and most labeling; reuses computation (design intent, partly tested) | Triage accuracy in Section @sec:graphs; run time and energy estimates in Section @sec:sustain |
| SDG 12: Responsible Consumption and Production | 12.6: integrate sustainability information into reporting | Sustainability assessment of the project with indicators and stated limits | Reports energy, emissions, privacy and inclusion with method and evidence (tested output) | Section @sec:sustain |

The link to Goal 9 is the most direct. The project develops and evaluates a new technical capability for keeping deployed models reliable, which is what target 9.5 describes and its monitoring makes digital infrastructure that depends on models more dependable, in the spirit of target 9.4. The link to Goal 12 rests on efficiency: a monitor that tells a team when retraining will not help and that needs labels for only a few hundred rows, saves computation and human labeling effort. The size of these savings in a real deployment has not been measured, so this report claims them as design intent and expected contribution only. Section @sec:sustain returns to both goals with the evidence gathered during the project.
