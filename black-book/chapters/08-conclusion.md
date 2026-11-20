# Conclusion {#ch:conclusion}

This project set out to turn a drift alarm into a decision. ResilientAI detects drift, estimates the lost accuracy, locates the features that moved and names the drift type, so that a monitoring team knows whether to reweight, recalibrate, collect fresh labels or check its labeling process.

The central result is that hypothesis tests with a stated error rate can name the drift type from label-free tests and a few hundred late labels. On injected drift the procedure named the type in \res{bench-a-ours-min} to \res{bench-a-ours-max}% of windows, beat every rule from monitoring practice and kept its false alarms below their bound. Unlike a learned meta-classifier, it carried over to drift mechanisms held out from its design. On four real datasets it raised no false verdict on any control window and traced documented events. The project met all its deliverables and its paper was accepted at ICMMDU 2026.

## Limitations {#sec:limitations}

The main limitations are the following.

- **One type per window.** Real windows such as ACS Income 2023 mix several types, but the procedure reports only the first it finds.
- **Class-conditional label noise.** The audit often mistakes noise that depends on the true class for concept drift, since a null model built on confidence alone cannot separate the two.
- **Optimistic estimates.** The accuracy estimate fails when the model stays confident while its accuracy falls.
- **Weak supporting stages.** The reliability fusion adds little beyond confidence and the triage needs an earlier labeled window.
- **Scope.** Deep models, text data and real-time streams remain untested.

## Future Scope {#sec:future}

1. **An audit conditioned on the full model output**, such as cells of predicted class and confidence, to separate class-conditional label noise from concept drift.
2. **Benchmark windows that mix several types** and tests on text and deep models.
3. **A pilot deployment** with a monitoring team, with a usability study, metered energy use and a fairness check.
