---
title: Additional file 1. Supplementary material for "Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models"
author: Rahul Guhagarkar; 1*
author: Nathan Cherian; 1
author: Alok Pal; 1
author: Akul Patre; 1
author: Sanjay Mirchandani; 1
affiliation: 1; Department of Computer Engineering, Vivekanand Education Society's Institute of Technology, Hashu Advani Memorial Complex, Collector's Colony, Chembur, Mumbai 400074, India
corresponding: 2023.rahul.guhagarkar@ves.ac.in
note: Section, figure, table and equation numbers without the prefix S refer to the main paper.
---

Eight topics that the main paper only touches on are expanded here. Section @sec:budget asks how many delayed labels the audit needs before its diagnosis settles. Section @sec:remediation breaks the remediation triage down by real setting, while Section @sec:relp records how the relationship codes of the American Community Survey (ACS) were matched across their 2019 redesign. Section @sec:dashboard presents the dashboard in which the pipeline displays its results. Section @sec:seeds shows how much the benchmark results vary over seeds and states. The last three sections belong to the comparison with published methods and to the added real control windows. Section @sec:pubtypes breaks the published methods down by drift type. Section @sec:realaudits gives the audit and the published methods on every real window. Section @sec:controls counts the alarms on the added control windows.

# Size of the delayed audit {#sec:budget}

The audit stage of Section @m:sec:diagnosis needs late labels. Labels cost money, so it matters how many are enough. The paper uses \res{acs-audit-n} labels throughout. Fig. @fig:budget shows how the share of correctly diagnosed windows changes with the size of the audit on ACS Income design A with logistic regression (LR).

![Share of correctly diagnosed windows on ACS Income design A with LR against the number of audit labels. The shaded bands are 95% Wilson intervals](FigS1.png){#fig:budget width=83.5}

With 200 labels, concept drift is identified in \res{b-inc-a-lr-budget-concept-200}% of windows and label noise in \res{b-inc-a-lr-budget-labelnoise-200}%. With 600 labels the two rates reach \res{b-inc-a-lr-budget-concept-600}% and \res{b-inc-a-lr-budget-labelnoise-600}%. Going on to 1000 labels adds little (\res{b-inc-a-lr-budget-concept-1000}% and \res{b-inc-a-lr-budget-labelnoise-1000}%). The 600 labels of the paper therefore sit where more labels stop paying off. The control windows are diagnosed correctly in the same share of cases at every audit size.

\newpage

# Remediation triage by setting {#sec:remediation}

Section @m:sec:res-reliability of the paper summarizes how often the triage of Section @m:sec:triage gives the right advice. Table @tab:remediation breaks this summary down by real setting and model family, so that the source of each right or wrong verdict can be seen.

Table: Remediation triage on the real windows. n is the number of windows; Significant gains counts the windows in which a strategy significantly raised holdout accuracy, by importance weighting (IW), retraining on the most recent labeled window (Recent) or retraining on labels of the window itself (Labels); n/a marks settings without an earlier window. Escalated counts the windows in which the triage recommended a retrain, Truly helps those in which a cheap retrain did help and Correct the windows in which the advice was right. Rule counts the windows in which the simple rule of retraining exactly when an earlier labeled window exists was right {#tab:remediation}
<<gen:tab_remediation>>

Where an earlier labeled window exists, retraining on it helps in almost every temporal window. The triage escalates in those windows. The geographic windows of the census tasks have no earlier window. There, importance weighting rarely helps and the triage mostly advises against a retrain. Most of the remaining wrong verdicts come from CLEAR-10 with LR and from the geographic windows of ACS Employment. The simple rule in the last column is right about as often as the triage. This is why the paper reports the triage as a negative result.

# Relationship codes across the 2019 redesign {#sec:relp}

The ACS windows run from 2014 to 2023, but one of their features changed its coding halfway through. From 2019 the Census Bureau replaced the relationship variable RELP with RELSHIPP, whose codes split spouses and partners by sex [@census2019pums]. To compare windows before and after 2019, we map the RELSHIPP codes back to RELP by matching the code labels of the 2018 and 2019 data dictionaries. Table @tab:relp lists the mapping as the code applies it.

Table: Mapping from RELSHIPP (2019 on) back to RELP (2014 to 2018) {#tab:relp}
<<code:relp_map>>

RELP 11 (roomer or boarder) has no successor, so it never occurs from 2019 on. The loss of this category is itself a documented change that the localization can pick up.

\newpage

# The monitoring dashboard {#sec:dashboard}

A diagnosis is only useful if the team can read it. Every stage of the pipeline therefore writes its results to one file, which an interactive dashboard presents. Fig. @fig:dashboard shows two of its views for ACS Income with LR.

![The dashboard of the pipeline for ACS Income with LR. (a) The overview: dataset, task and model selectors, the headline results and the five steps of the pipeline, each of which opens a detailed view. (b) The drift type step: for every window, the answer to each question of the decision path in Fig. 2 of the paper (filled circle yes, open circle no, small dot not reached) and the resulting verdict, followed by a summary sentence computed from the results](FigS2.png){#fig:dashboard width=148}

Panel (b) applies the decision path of Fig. @m:fig:decision to the real California (CA) windows. CA 2015 passes every test of the label-free stage. The KS detector in Table @m:tab:income of the paper does raise an alarm on CA 2015. The two do not contradict each other. The detector corrects only over the numeric features, while the label-free stage tests all features together with the other two blocks in one weighted Holm family (Section @m:sec:diagnosis). The audit then finds no significant drop in accuracy, so the verdict is no drift. In CA 2016, CA 2018 and CA 2019 the predicted labels stay where they were. The feature tests still reject and the shift survives the prior correction, so these windows are covariate shift. All other windows answer yes to every label-free question and are covariate shift as well. Each view of the dashboard opens with the question it answers and closes with a summary sentence of this kind, so a team can follow the diagnosis without reading the code.

# Spread over seeds and states {#sec:seeds}

A share pooled over many windows can hide how much it moves from one run to the next. The shares in Tables @m:tab:methods and @m:tab:mechanisms of the paper pool the windows of all five states and ten seeds. Here they are taken apart. Table @tab:seedsmethods shows how much the share of correctly typed windows varies. Table @tab:seedsmechanisms does the same for the design B mechanisms. Each cell gives the mean and standard deviation of the share over the ten seeds, where each seed pools its five states. The interval in brackets treats the state as the cluster. It is a 95% t interval with four degrees of freedom over the five state shares, cut at 0 and 100%. With only five clusters, these intervals are wide.

Table: Share of benchmark windows with the correct drift type over seeds and states (%). Inc. and Emp. stand for ACS Income and ACS Employment, A and B for the two designs {#tab:seedsmethods}
<<gen:tab_seeds_methods>>

Table: Correct diagnosis by design B mechanism over seeds and states (%) {#tab:seedsmechanisms}
<<gen:tab_seeds_mechanisms>>

The two tables added in the revision get the same treatment. Table @tab:seedspublished covers the published methods of Table @m:tab:published of the paper. Table @tab:seedsnoise covers the label noise mechanisms of Table @m:tab:noise, where each seed pools its five states and the four task and model configurations.

Table: Share of benchmark windows with the correct drift type for the published methods over seeds and states (%). Label-free + CL is our label-free stage followed by confident learning {#tab:seedspublished}
<<gen:tab_seeds_published>>

Table: Share of label noise windows named label noise over seeds and states (%) {#tab:seedsnoise}
<<gen:tab_seeds_noise>>

\floatbarrier

# Published methods by drift type {#sec:pubtypes}

An overall share does not say which drift types a method gets right. Table @tab:publishedtypes therefore splits the shares of Table @m:tab:published of the paper by injected type. For each method it gives the share of windows of each type that were typed correctly, pooled over the four configurations of each design. Design B has no control windows, so its first column is missing.

Table: Correct drift type by injected type for the published methods, pooled over task and model (%). Cov. is covariate shift, Conc. concept drift and Noise label noise {#tab:publishedtypes}
<<gen:tab_published_types>>

Some zeros follow from the design of the methods. The method of Roschewitz et al. has no type for concept drift or label noise. DetectShift has none for label noise. DetectShift also reads most design A covariate windows as concept drift. Design A moves feature values while the labels stay, which changes $P(Y\mid X)$ as well (Section @m:sec:res-published).

# The audit and the published methods on the real windows {#sec:realaudits}

In the paper the audit runs only when the label-free stage finds nothing. A window with a covariate verdict is therefore never audited, even though its labels may have changed too. Table @tab:realaudits shows what the audit would say on every one of the \res{realaud-n} real windows of both models. Next to it stand the final verdict of our procedure and the verdicts of the three published methods. Each window uses the audit sample of the paper. In the table $\Delta$ is the audit accuracy minus the model's accuracy on the control window (points), Audit is the verdict of the audit alone and Ours the final verdict of the procedure. Ros. is the method of Roschewitz et al. and CL our label-free stage followed by confident learning. DS is DetectShift, which does not use the model and so gives one verdict. Cov. stands for covariate shift, Conc. for concept drift and Noise for label noise. The audit names no drift in \res{realaud-audit-none} windows, concept drift in \res{realaud-audit-concept} and label noise in \res{realaud-audit-labelnoise}.

Table: The audit and the published methods on the real windows. A dash means no drift. Where the two models differ, a cell gives the LR and the GB verdict {#tab:realaudits}
<<gen:tab_real_audits>>

The four datasets behave quite differently. On ACS Employment, whose accuracy hardly moved, the audit finds no drop in any window. On the gas sensor array it finds one in every batch and mostly names concept drift. On ACS Income it finds a drop in most windows from 2018 on. There it names concept drift or label noise, as the change of the labels against the fixed income threshold suggests. On CLEAR-10 it finds a drop only in bucket 10. The final verdict of our procedure stays covariate shift in all these windows, because the label-free stage rejects first (Section @m:sec:discussion). DetectShift names concept drift in \res{realpub-detectshift-concept} windows and covariate shift in \res{realpub-detectshift-covariate}. The method of Roschewitz et al. names covariate shift in \res{realpub-roschewitz-covariate} windows and prior shift in \res{realpub-roschewitz-prior}, both of them ACS Income 2017. CL follows our label-free stage and adds label noise in \res{realpub-confidentlearning-labelnoise} window, CLEAR-10 bucket 3 with LR.

\floatbarrier

# More control windows on real data {#sec:controls}

A control window holds no drift, so every alarm on it is false. Each real dataset has only one such window in the paper, which is too few to judge the false alarm rate. Table @tab:controls adds \res{ctrl-per} control windows for each dataset and model. For each of them the reference data are split again with a new seed. The model is refitted on the new training part and the new test part is the control window. Every column counts the windows with an alarm or with a verdict other than no drift.

Table: Alarms on the added control windows of the real datasets, \res{ctrl-per} for each dataset and model. Conf. is the confidence test, DC the domain classifier, Ros. the method of Roschewitz et al., DS DetectShift and CL our label-free stage followed by confident learning {#tab:controls}
<<gen:tab_controls>>

Our procedure raised a false alarm on \res{ctrl-ours-k} of the \res{ctrl-n} windows (\res{ctrl-ours-pct}%, 95% CI \res{ctrl-ours-ci}). The bound for the whole procedure is $2\alpha$, since a verdict passes two stages that are each tested at level $\alpha$. The label-free stage raised \res{ctrl-ours-labelfree-k} of the false alarms (\res{ctrl-ours-labelfree-pct}%, 95% CI \res{ctrl-ours-labelfree-ci}) and the audit \res{ctrl-ours-audit-k} (\res{ctrl-ours-audit-pct}%, 95% CI \res{ctrl-ours-audit-ci}). Both intervals contain $\alpha=5$%, the level at which each detector is tested on its own. Our label-free stage followed by CL raised \res{ctrl-confidentlearning-k} false alarms (\res{ctrl-confidentlearning-pct}%, 95% CI \res{ctrl-confidentlearning-ci}).

\floatbarrier

# References {-}
