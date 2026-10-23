---
title: Supplementary Material for "Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models"
author: Rahul Guhagarkar; 1*
author: Nathan Cherian; 1
author: Alok Pal; 1
author: Akul Patre; 1
author: Sanjay Mirchandani; 1
affiliation: 1; Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: 2023.rahul.guhagarkar@ves.ac.in
note: Section, figure, table and equation numbers without the prefix S refer to the main paper.
---

Four topics that the main paper only touches on are expanded here. Section @sec:budget asks how many delayed labels the audit needs before its diagnosis settles. Section @sec:remediation breaks the remediation triage down by real setting, while Section @sec:relp records how the relationship codes of the American Community Survey (ACS) were matched across their 2019 redesign. The last section, Section @sec:dashboard, presents the dashboard in which the pipeline displays its results.

# Size of the delayed audit {#sec:budget}

The audit stage of Section @m:sec:diagnosis needs late labels. Labels cost money, so it matters how many are enough. The paper uses \res{acs-audit-n} labels throughout. Fig. @fig:budget shows how the share of correctly diagnosed windows changes with the size of the audit on ACS Income design A with logistic regression (LR).

![Share of correctly diagnosed windows on ACS Income design A with LR against the number of audit labels. The shaded bands are 95% Wilson intervals](FigS1.png){#fig:budget width=83.5}

With 200 labels, concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows and label noise in \res{b-inc-a-lr-budget-labelnoise-200}%. With 600 labels the two rates reach \res{b-inc-a-lr-budget-concept-600}% and \res{b-inc-a-lr-budget-labelnoise-600}%. Going on to 1,000 labels adds little (\res{b-inc-a-lr-budget-concept-1000}% and \res{b-inc-a-lr-budget-labelnoise-1000}%). The 600 labels of the paper therefore sit where more labels stop paying off. The control windows are diagnosed correctly in the same share of cases at every audit size.

\newpage

# Remediation triage by setting {#sec:remediation}

Section @m:sec:res-reliability of the paper summarizes how often the triage of Section @m:sec:triage gives the right advice. Table @tab:remediation breaks this summary down by real setting and model family, so that the source of each right or wrong verdict can be seen.

Table: Remediation triage on the real windows. n is the number of windows; Significant gains counts the windows in which a strategy significantly raised holdout accuracy, by importance weighting (IW), retraining on the most recent labeled window (Recent) or retraining on labels of the window itself (Labels); n/a marks settings without an earlier window. Escalated counts the windows in which the triage recommended a retrain, Truly helps those in which a cheap retrain did help and Correct the windows in which the advice was right {#tab:remediation}
<<gen:tab_remediation>>

Where an earlier labeled window exists, retraining on it helps in almost every temporal window. The triage escalates in those windows. The geographic windows of the census tasks have no earlier window. There, importance weighting rarely helps and the triage mostly advises against a retrain. Most of the remaining wrong verdicts come from CLEAR-10 with LR and from the geographic windows of ACS Employment.

# Relationship codes across the 2019 redesign {#sec:relp}

The ACS windows run from 2014 to 2023, but one of their features changed its coding halfway through. From 2019 the Census Bureau replaced the relationship variable RELP with RELSHIPP, whose codes split spouses and partners by sex [@census2019pums]. To compare windows before and after 2019, we map the RELSHIPP codes back to RELP by matching the code labels of the 2018 and 2019 data dictionaries. Table @tab:relp lists the mapping as the code applies it.

Table: Mapping from RELSHIPP (2019 on) back to RELP (2014 to 2018) {#tab:relp}
<<code:relp_map>>

RELP 11 (roomer or boarder) has no successor, so it never occurs from 2019 on. The loss of this category is itself a documented change that the localization can pick up.

\newpage

# The monitoring dashboard {#sec:dashboard}

A diagnosis is only useful if the team can read it. Every stage of the pipeline therefore writes its results to one file, which an interactive dashboard presents. Fig. @fig:dashboard shows two of its views for ACS Income with LR.

![The dashboard of the pipeline for ACS Income with LR. (a) The overview: dataset, task and model selectors, the headline results and the five steps of the pipeline, each of which opens a detailed view. (b) The drift type step: for every window, the answer to each question of the decision path in Fig. 2 of the paper (filled circle yes, open circle no, small dot not reached) and the resulting verdict, followed by a summary sentence computed from the results](FigS2.png){#fig:dashboard width=148}

Panel (b) applies the decision path of Fig. @m:fig:decision to the real California (CA) windows. CA 2015 passes every label-free test. The audit then finds no significant drop in accuracy, so the verdict is no drift. In CA 2016, CA 2018 and CA 2019 the predicted labels stay where they were. The feature tests still reject and the shift survives the prior correction, so these windows are covariate shift. All other windows answer yes to every label-free question and are covariate shift as well. Each view of the dashboard opens with the question it answers and closes with a summary sentence of this kind, so a team can follow the diagnosis without reading the code.

# References {-}
