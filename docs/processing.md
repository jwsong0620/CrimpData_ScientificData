# Processing and provenance

The source monitor records a reference row followed by a measurement row.
`metadata/record_correspondence.csv` identifies the measurement row associated
with every retained CSV row. One-based source data-row positions exclude the
descriptive first line and header; physical CSV line numbers include both.

## Trimming code

`scripts/trim_exports.py` is a command-line adaptation of the supplied historical
trimming script. The algorithm applies forward-fill to all imported columns,
assigns labels to row pairs and removes pairs labelled Unknown. It exports 200
waveform columns plus the intermediate Results field. Reference and measurement
rows remain distinct, using g1/g2 for acceptance and b1/b2 for rejection.

The adaptation removes hard-coded workstation paths and automatic deletion of
output folders. It uses `ffill()` instead of the deprecated pandas method argument.
It does not claim to be the original file byte for byte. The original script's
SHA-256 is `1f3b107d97a559f9e1283260db30f28e3a8431862a31da6a96c682be6022df81`.

Counter rules are implemented in `counter_labels()` in
`validate_source_correspondence.py` and shared by trimming and reconstruction:

1. Initialize previous Good and Bad values to zero.
2. When both current counters are zero, reset both previous values and assign Unknown.
3. A first pair with nonzero counters establishes the initial values and is Unknown.
4. Otherwise, check Good increment of one before checking Bad increment of one.
   The first branch takes precedence if both increase by one.
5. Update only the previous counter belonging to the selected branch.
6. Assign Unknown immediately before a zero/zero reset and at the last pair.
7. If neither increment rule is met, assign Unknown.

These are the supplied script's operational rules, not a general recommendation
for counter-based labelling. The counters used to determine labels are read from
the upper/reference rows. Although forward-fill affects all imported columns in
the historical procedure, all 200 retained waveform entries are already present
in the original measurement rows; direct comparison found no changes to them.

## Final six files

Production-segment selection and conversion of measured-row g2/b2 labels to 0/1
occurred after trimming. The historical downstream selection script was not
retained. `reconstruct_release.py` provides a reproducible **mapped extraction**
from supplied source exports. It copies the 200 source values and reconstructs
labels from the counters, using the published correspondence table to select rows.
It does not recover why other rows were excluded. Newly serialized CSV bytes may
differ while their numeric values and row order remain identical.

## Separate levels of verification

- `run_checks.py` without source inputs checks public CSV integrity and mapping
  coverage, not agreement with undisclosed source exports.
- With `--source-dir`, it checks all mapped source values, label decisions and
  retained order. The input filenames and hashes are recorded in the report.
- Neither operation verifies the physical quality of every product. Normal and
  abnormal denote operational CFM labels. Physical inspection coverage is separate.

The reference source report documents a local check against redacted copies,
after the retained fields were compared with the original exports. Those copies
omit unrelated fields and replace the descriptive preamble. Missing trailing
fields in some reference rows were represented as empty fields, without numerical
imputation. The source report is not independently reproducible from this public
archive alone. See [source access](source_access.md).
