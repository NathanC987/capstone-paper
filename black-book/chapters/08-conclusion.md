# Conclusion {#ch:conclusion}

This project set out to turn a drift alarm into a decision. ResilientAI watches a deployed classifier, tests every new window of production data for a change, estimates the accuracy the model is likely to have, locates the features that moved and names the type of drift, so that a monitoring team knows whether to reweight, recalibrate, collect fresh labels or check its labeling process. It also explains the change, scores the trust due to each prediction, advises whether a cheap retrain would help and presents everything in a dashboard.

The central result is that hypothesis tests with a stated error rate can name the drift type from label-free tests and a few hundred late labels. The new audit test separates concept drift from label noise by asking whether the change in errors depends on a feature beyond what the model's confidence explains. On injected drift the procedure named the type in \res{bench-a-ours-min} to \res{bench-a-ours-max}% of windows, beat every rule from monitoring practice and kept its false alarms below their bound. Unlike a learned meta-classifier, it carried over to drift mechanisms held out from its design, because its tests encode the definitions of the types rather than the look of past examples. On four real datasets it raised no false verdict on any control window and traced documented events, from new occupation codes in the census to aging gas sensors.

The project met the deliverables of Section @sec:deliverables. Along the way it also showed the value of practices that are easy to skip in a student project: fixing the protocol before the evaluation, generating every reported number from stored outputs and testing the error rates of the statistics themselves. Those practices caught real errors and made it possible to correct them honestly.

## Limitations {#sec:limitations}

The system has the following limitations, each visible in the results of Chapter @ch:results.

- **One type per window.** Each benchmark window holds a single drift type, while real windows such as ACS Income 2023 mix several. The procedure reports the first type it finds.
- **Idealized types.** Sensor aging changes $P(X\mid Y)$ and, through it, $P(Y\mid X)$, yet the procedure reports it as covariate shift, because the four types are an idealization of real change.
- **Class-conditional label noise.** The audit often mistakes noise that depends on the true class for concept drift, since a null model built on confidence alone cannot separate the two.
- **Drift without loss.** The audit lets through drift that does not hurt accuracy, such as the raised income threshold. This is by design but may surprise a user.
- **Sampling error of the weights.** The weighted residual tests do not account for the sampling error of the BBSE weights.
- **Large samples.** At several hundred thousand rows almost any shift is significant, so each decision must be read with its effect size.
- **Optimistic estimates.** The accuracy estimate fails when the model stays confident while its accuracy falls, as on the gas sensor data and is best read as an upper bound.
- **Weak supporting stages.** The reliability fusion adds almost nothing beyond confidence and the triage has low recall when no earlier labeled window exists.
- **Scope.** Deep models trained end to end, text data and real-time streams remain untested and the system has not been used by a monitoring team outside the project.

## Future Scope {#sec:future}

The limits above point to realistic next steps.

1. **An audit conditioned on the full model output**, such as cells of predicted class and confidence, to separate class-conditional label noise from concept drift. The ablation in Section @sec:graphs suggests this helps on held-out drift and it should be tested on a fresh benchmark design to avoid bias.
2. **A model of the sampling error of the BBSE weights** in the label shift consistency test.
3. **Benchmark windows that mix several types**, with a diagnosis that can report more than one.
4. **Text and deep models**, by applying the same tests to embeddings of text and to models fine-tuned on the production stream.
5. **Streaming operation**, with sequential tests that keep the error rate over an open-ended sequence of windows.
6. **A pilot deployment** with a monitoring team, together with a usability study, metered energy use and a fairness check of the monitored models, which would also complete the sustainability evidence of Section @sec:sustain.
7. **Integration with existing monitoring platforms**, so that the diagnosis can run beside the detectors teams already use.
