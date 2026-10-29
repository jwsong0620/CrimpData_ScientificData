# Evaluation guidance

For evaluation within a production sequence, use earlier rows for training,
later rows for validation and a final block for testing. Retain row order and
report boundaries and class counts. Randomly distributing adjacent operations
between training and test data can share local signal conditions and drift trends.

Hold out complete files to evaluate transfer between production jobs. When testing
an unseen 18 AWG configuration, hold out both 18 AWG files if the intended claim is
generalization to an unseen wire gauge. Gauge, terminal, applicator and settings
are coupled; these data do not isolate a causal wire-gauge effect.

Fit scaling, feature selection and other learned preprocessing on training data.
Select model settings and thresholds using training/validation data only. If
validation contains no rejected events, specify a threshold rule based on an
accepted-validation false-alarm target rather than selecting it on test labels.
State the information available to any adaptive method and prevent future records
or test labels from guiding its updates.

Report test class counts, the confusion matrix, rejected-class recall and precision,
and the false-positive rate among accepted operations. Include per-file results.
Always predicting normal yields about 99.74% accuracy on the complete collection,
so overall accuracy alone is not useful. With only 26 rejections, report event
counts and uncertainty assumptions; row independence is not guaranteed.

The 4 May file contains no rejected operation. It can measure false alarms against
CFM-accepted labels, but cannot estimate rejected-class recall or ROC AUC. Precision
is undefined if no rejections are predicted; with false alarms alone it is zero
and says nothing about detection sensitivity.

Performance measures agreement with CFM decisions, subject to the limited documented
inspection coverage. Drift descriptors are descriptive differences from the first
accepted waveform, not annotated change points or identified physical causes.
