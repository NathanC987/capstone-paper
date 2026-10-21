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

This supplement gives three pieces of detail that support the main paper: how the size of the delayed audit affects the diagnosis, the remediation triage in every real setting and the mapping of the ACS relationship codes across the 2019 redesign.

# Size of the delayed audit {#sec:budget}

The audit stage of Section @m:sec:diagnosis separates concept drift from label noise with a few hundred late labels. The paper uses \res{acs-audit-n} labels throughout. Fig. @fig:budget shows how the share of correctly diagnosed windows changes with the number of audit labels on ACS Income design A with logistic regression (LR).

![Share of correctly diagnosed windows on ACS Income design A with LR against the number of audit labels. The shaded bands are 95% Wilson intervals](FigS1.png){#fig:budget width=83.5}

Concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows with 200 labels and \res{b-inc-a-lr-budget-concept-600}% with 600, while label noise is identified in \res{b-inc-a-lr-budget-labelnoise-200}% and \res{b-inc-a-lr-budget-labelnoise-600}%. With 1,000 labels neither rate rises much further (\res{b-inc-a-lr-budget-concept-1000}% and \res{b-inc-a-lr-budget-labelnoise-1000}%), so the 600 labels used in the paper lie where the gain from more labels has largely flattened. The control windows are diagnosed correctly in the same share of cases at every audit size.

\newpage

# Remediation triage by setting {#sec:remediation}

Section @m:sec:res-reliability summarizes how often the triage of Section @m:sec:triage gives the right advice. Table @tab:remediation shows the result for every real setting and both model families.

Table: Remediation triage on the real windows. n is the number of windows; Significant gains counts the windows in which a strategy significantly raised holdout accuracy, by importance weighting (IW), retraining on the most recent labeled window (Recent) or retraining on labels of the window itself (Labels); n/a marks settings without an earlier window. Escalated counts the windows in which the triage recommended a retrain, Truly helps those in which a cheap retrain did help and Correct the windows in which the advice was right {#tab:remediation}
<<gen:tab_remediation>>

The pattern behind the summary in the paper is visible here. Wherever an earlier labeled window exists, retraining on it helps in almost every temporal window and the triage escalates accordingly. The geographic windows of the census tasks have no earlier window. Importance weighting rarely helps there. The triage advises against retraining in most of them. The remaining wrong verdicts fall mostly on CLEAR-10 with LR and on the geographic ACS Employment windows.

# Relationship codes across the 2019 redesign {#sec:relp}

From 2019 the Census Bureau replaced the relationship variable RELP with RELSHIPP, which splits spouses and partners by sex [@census2019pums]. To compare windows before and after 2019, the RELSHIPP codes are mapped back to RELP by matching the code labels of the 2018 and 2019 data dictionaries. Table @tab:relp lists the mapping that the code applies.

Table: Mapping from RELSHIPP (2019 on) back to RELP (2014 to 2018) {#tab:relp}
<<code:relp_map>>

Same-sex and opposite-sex spouses both map to husband/wife and both partner codes to unmarried partner. RELP 11 (roomer or boarder) has no successor, so it never occurs from 2019 onward. This removed category is itself a documented change that the localization can detect.

# References {-}
