# Source access

The public repository contains the six final waveform CSVs and their mapping to
five source exports. It does not contain the complete original exports or their
redacted review copies. Those copies also contain operations outside the six
disclosed sequences; permission to distribute them has not been established.

Terminal codes, defect photographs and detailed defect categories are not supplied.
The absence of these items does not prevent validation of the included CSV files.
It does limit the scope of independently reproducible source and physical-quality
checks.

`validation/reference/source_validation_report.json` records a local comparison
against redacted source copies. Treat it as an author-produced report. Original
and redacted file hashes in `metadata/source_manifest.json` identify files but
cannot prove authenticity or replace access to the files themselves.

Reviewer source access: **not yet arranged**. An authorized reviewer package may
be shared separately through a preview/download link. No claim of existing
reviewer access is made here. Do not commit confidential reviewer links or source
copies to the public repository.

With authorized source files available locally:

```sh
python scripts/run_checks.py --source-dir /path/to/authorized/exports
python scripts/reconstruct_release.py --source-dir /path/to/authorized/exports --output-dir /path/to/new/reconstructed-data
python scripts/plot_waveform_figures.py --input-dir data --source-dir /path/to/authorized/exports --output-dir figures/generated
```

The first command adds source checks; the second recreates the mapped six files;
the third also produces Figure 2. Repeat `--source-dir` when files are in multiple
folders. The source checker and mapped reconstruction require only the Python
standard library. The waveform plotting command needs `requirements.txt`.

Source copies must preserve all reference/measurement row positions and counter
history, including initialization and resets, for the published mapping and
counter logic to remain valid. Removing unselected rows changes these coordinates.
Confidential fields can be omitted only if required counter, timestamp and waveform
columns are retained. Any redaction must be documented rather than represented
as an unchanged original export.
