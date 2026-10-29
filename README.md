# Industrial crimping waveforms from routine production

Six production sequences contain **9,829 crimping waveforms** from Sungchangsa
Co., Ltd., South Korea: 9,803 CFM-accepted and 26 CFM-rejected operations across
five wire gauges. No defects were deliberately introduced for data collection.
Each row contains one 200-point waveform and its operational CFM label.

Prepared version: **1.0.0**. The repository and DOI fields remain unset until
the author publishes the package. This repository does not claim journal acceptance.

| File | AWG | Operations | Normal (0) | Abnormal (1) |
|---|---:|---:|---:|---:|
| 20230426.csv | 18 | 1,485 | 1,484 | 1 |
| 20230427.csv | 16 | 1,026 | 1,024 | 2 |
| 20230428.csv | 18 | 2,956 | 2,946 | 10 |
| 20230503.csv | 20 | 1,207 | 1,199 | 8 |
| 20230504.csv | 14 | 1,288 | 1,288 | 0 |
| 20230505.csv | 22 | 1,867 | 1,862 | 5 |

## Start with the integrity check

From the repository root, with Python 3.10 or later:

```sh
python scripts/run_checks.py
```

No additional Python packages are needed for these checks. Outputs are written
to `validation/rerun/`. The expected totals are 9,829 records, 1,965,800 waveform
values and 26 rejection labels. The command checks file hashes, schema, missing
values, duplicates and correspondence-table coverage. It explicitly reports
source matching as **not run** unless source exports are supplied.

## Reproduce the waveform and drift figures

Python 3.12 was used for the tested plotting environment:

```sh
python -m pip install -r requirements.txt
python scripts/plot_waveform_figures.py --input-dir data --output-dir figures/generated
python scripts/plot_production_drift.py --input-dir data --output-dir figures/generated --summary-dir validation/rerun/drift
```

These commands reproduce Figures 3 and 4. The fixed first accepted waveform
used for the drift plot is distinct from the monitor's adaptive reference.
Figure 2 requires the original paired reference waveform; see
[source access](docs/source_access.md). Figure 1 is an author-supplied schematic.

## Files

- `data/`: the six unchanged CSV files.
- `metadata/`: field definitions, production context, retained-to-source row
  correspondence, checksums and tested runtime information.
- `scripts/`: validation, figure generation, safe trimming, mapped reconstruction
  and release-archive preparation.
- `validation/reference/`: validation reports produced during local preparation.
  The source report records an author-side check and is identified accordingly.
- `figures/reference/`: Figures 3 and 4 generated from the six included CSVs.
- `docs/`: reproduction steps, label and processing details, reuse guidance,
  source-access scope and deposition instructions.
- `licenses/`: full CC BY 4.0 and MIT licence texts.

## Reading the data

The CSV header is `data1,...,data200,label`. The waveform columns are ordered
measurement points within one crimping operation. The rows preserve retained
operation order within each file. These axes do not establish elapsed time or
calibrated force. Values remain on the native instrument export scale.
Filename dates serve as dataset identifiers and are not verified timestamps.
Use filename and one-based data-row number as a record ID, e.g. `20230426.csv:1`.

All files use the same JYP-P700 press, True Soltec CFM-Lite monitor and frame-mounted
PSS50 sensor. Wires, terminals, applicators and settings vary with the production
job; the two 18 AWG sequences used the same wire, terminal and applicator.
Terminal product codes are not disclosed. Gauge alone is not a controlled factor.

## Labels and reuse

Normal/abnormal mean CFM acceptance/rejection. Production personnel checked flagged
products and reported defects, but record-specific inspection coverage and criteria
are not available. The labels are not independent physical-quality ground truth
for every operation. The 26 rejection events are sparse; the 4 May file contains
none. See [reuse guidance](docs/reuse.md) for temporal evaluation, avoiding data
leakage and interpreting class-specific metrics.

## Provenance and access

The published CSVs and correspondence metadata are included. The five original
instrument exports are **not** included. The local comparison found no mismatch
in values, labels or retained order. Independent source-level verification requires
separate source access; the published report alone is not a substitute for it.
The mapping reproduces the retained records, but does not recover the historical
selection rationale. See [processing](docs/processing.md) and
[source access](docs/source_access.md).

## Licence and citation

Data, metadata, documentation and derived outputs: **CC BY 4.0**.
Python scripts: **MIT**. See [LICENSE](LICENSE) for scope and attribution.
Dataset creators are Jinwoo Song and Heung Soo Kim; production data were provided
by Sungchangsa Co., Ltd. Citation metadata are in [CITATION.cff](CITATION.cff).
Add the version-specific Zenodo DOI to citations once it has been assigned.

## Publication preparation

The intended route is GitHub for version control and a Zenodo Dataset record
for a persistent, citable snapshot. The journal does not require this particular
repository or folder layout. See [journal guidance and examples](docs/deposition.md)
and [the Korean upload instructions](docs/UPLOAD_KO.txt).
