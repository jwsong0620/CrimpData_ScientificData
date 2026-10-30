# Crimping waveforms from routine wire harness production

This dataset contains **9,829 crimping waveforms** collected during routine
production at Sungchangsa Co., Ltd., South Korea. Six production sequences cover
**five wire gauges (14–22 AWG)** and include **26 CFM-rejected operations**.
Defects arose during production without deliberate fault introduction.

The data support evaluation across wire sizes and production configurations,
including rare defects and changes in waveforms over successive operations.

## Dataset

| File | AWG | Operations | CFM accepted (0) | CFM rejected (1) |
|---|---:|---:|---:|---:|
| 20230426.csv | 18 | 1,485 | 1,484 | 1 |
| 20230427.csv | 16 | 1,026 | 1,024 | 2 |
| 20230428.csv | 18 | 2,956 | 2,946 | 10 |
| 20230503.csv | 20 | 1,207 | 1,199 | 8 |
| 20230504.csv | 14 | 1,288 | 1,288 | 0 |
| 20230505.csv | 22 | 1,867 | 1,862 | 5 |
| **Total** | | **9,829** | **9,803** | **26** |

Each CSV contains one row per crimping operation:

- `data1`–`data200`: the 200 measurement points of one waveform, in acquisition order.
- `label`: `0` for normal (CFM accepted), `1` for abnormal (CFM rejected).

Waveform values remain on the native instrument scale. Point numbers describe
positions within a waveform, not calibrated time or force. Filenames identify
the production sequences, and rows retain the order of the included operations.
A record can be identified by filename and one-based data-row number, such as
`20230426.csv:1`.

## Repository contents

| Folder | Contents |
|---|---|
| `data/` | Six waveform CSVs |
| `metadata/` | Variable definitions, production settings, source-row correspondence and checksums |
| `scripts/` | Data validation, processing and figure-generation code |
| `figures/reference/` | Waveform and drift figures |
| `validation/reference/` | Validation reports |
| `docs/` | Processing details and reuse guidance |

## Validate the data

Run from the repository root using Python 3.10 or later. No additional packages
are needed for validation.

```sh
python scripts/run_checks.py
```

Results are written to `validation/rerun/`. The original instrument exports are
not included; source-level comparison requires separately supplied files.
See [source verification](docs/source_access.md).

## Generate figures

The plotting scripts were tested with Python 3.12. Install the dependencies and
generate the waveform and production-drift figures:

```sh
python -m pip install -r requirements.txt
python scripts/plot_waveform_figures.py --input-dir data --output-dir figures/generated
python scripts/plot_production_drift.py --input-dir data --output-dir figures/generated --summary-dir validation/rerun/drift
```

See [processing details](docs/processing.md) and [evaluation guidance](docs/reuse.md)
for label interpretation, temporal evaluation and the small number of rejected operations.

## Licence and citation

Data, metadata and documentation: **CC BY 4.0**. Python code: **MIT**.
Full terms are in [LICENSE](LICENSE).

Please cite the dataset using [CITATION.cff](CITATION.cff) and acknowledge
Sungchangsa Co., Ltd. as the production data provider.
