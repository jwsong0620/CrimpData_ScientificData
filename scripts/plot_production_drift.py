"""Describe changes from each sequence's first CFM-accepted waveform.

Requires NumPy and Matplotlib. Inputs are six unchanged CSVs containing
data1..data200,label. This descriptive analysis fits no prediction model and
does not assign drift-onset or change-point ground truth.

Example:
  python plot_production_drift.py --input-dir DATA --output-dir FIGURES \
      --summary-dir SUMMARIES
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
import numpy as np


DATASETS = [
    ("A", "20230426.csv", 18, 1485, 1),
    ("B", "20230427.csv", 16, 1026, 2),
    ("C", "20230428.csv", 18, 2956, 10),
    ("D", "20230503.csv", 20, 1207, 8),
    ("E", "20230504.csv", 14, 1288, 0),
    ("F", "20230505.csv", 22, 1867, 5),
]
FILE_DATE_LABELS = dict(zip([row[1] for row in DATASETS],
                            ["26 Apr 2023", "27 Apr 2023", "28 Apr 2023",
                             "3 May 2023", "4 May 2023", "5 May 2023"]))
# These visible dates identify files, not independently verified acquisition dates.
WINDOW = 100


def read_data(path, expected_n, expected_rejected):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        expected_header = [f"data{i}" for i in range(1, 201)] + ["label"]
        if next(reader) != expected_header:
            raise ValueError(f"Unexpected columns in {path.name}")
        data = np.asarray([[float(v) for v in row] for row in reader], dtype=float)
    if data.shape != (expected_n, 201) or not np.isfinite(data).all():
        raise ValueError(f"Unexpected dimensions or non-finite value in {path.name}")
    x, labels = data[:, :200], data[:, 200]
    if not np.isin(labels, [0, 1]).all() or int((labels == 1).sum()) != expected_rejected:
        raise ValueError(f"Unexpected labels in {path.name}")
    return x, labels.astype(int)


def trailing_accepted_median(values, labels):
    """At position i (0-based), use accepted rows max(0,i-99)..i inclusive."""
    result = np.full(len(values), np.nan)
    for i in range(len(values)):
        start = max(0, i - WINDOW + 1)
        accepted = labels[start:i + 1] == 0
        if accepted.any():
            result[i] = np.median(values[start:i + 1][accepted])
    return result


def write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.summary_dir.mkdir(parents=True, exist_ok=True)

    all_records, summaries, provenance, plotted = [], [], [], []
    for sequence_id, filename, gauge, expected_n, expected_rejected in DATASETS:
        path = args.input_dir / filename
        x, labels = read_data(path, expected_n, expected_rejected)
        n = len(x)
        accepted = labels == 0
        ref_index = int(np.flatnonzero(accepted)[0])
        ref = x[ref_index]
        denominator = float(np.abs(ref).sum())
        if denominator <= 0:
            raise ValueError(f"Zero reference L1 norm in {filename}")
        l1 = np.abs(x - ref).sum(axis=1)
        relative = 100.0 * l1 / denominator
        peak = x.max(axis=1)
        peak_index = x.argmax(axis=1) + 1
        rolling = trailing_accepted_median(relative, labels)
        reference_id = f"{filename}:{ref_index + 1}"
        if l1[ref_index] != 0 or not np.isfinite(relative).all():
            raise ValueError(f"Distance validation failed in {filename}")

        for i in range(n):
            all_records.append({
                "record_id": f"{filename}:{i + 1}",
                "sequence_id": sequence_id,
                "filename": filename,
                "row_index": i + 1,
                "wire_gauge_awg": gauge,
                "label": int(labels[i]),
                "reference_record_id": reference_id,
                "reference_l1_norm_native": denominator,
                "l1_distance_native": float(l1[i]),
                "relative_l1_percent": float(relative[i]),
                "peak_value_native": float(peak[i]),
                "peak_index": int(peak_index[i]),
                "trailing_100_rows_label0_median_relative_l1_percent":
                    float(rolling[i]) if np.isfinite(rolling[i]) else "",
            })

        boundaries = [k * n // 4 for k in range(5)]
        first = np.arange(boundaries[0], boundaries[1])
        last = np.arange(boundaries[3], boundaries[4])
        first = first[accepted[first]]
        last = last[accepted[last]]
        if not len(first) or not len(last):
            raise ValueError(f"An endpoint quarter has no accepted records in {filename}")
        first_peak = float(np.median(peak[first]))
        last_peak = float(np.median(peak[last]))
        if first_peak <= 0:
            raise ValueError(f"Non-positive first-quarter peak median in {filename}")
        summaries.append({
            "sequence_id": sequence_id, "filename": filename, "wire_gauge_awg": gauge,
            "n_records": n, "n_label0": int(accepted.sum()),
            "n_label1": int((labels == 1).sum()),
            "reference_record_id": reference_id,
            "reference_l1_norm_native": denominator,
            "first_quarter_start_row": 1,
            "first_quarter_end_row": boundaries[1],
            "last_quarter_start_row": boundaries[3] + 1,
            "last_quarter_end_row": n,
            "first_quarter_n_label0": len(first),
            "last_quarter_n_label0": len(last),
            "first_quarter_label0_median_relative_l1_percent": float(np.median(relative[first])),
            "last_quarter_label0_median_relative_l1_percent": float(np.median(relative[last])),
            "relative_l1_median_change_percentage_points": float(np.median(relative[last]) - np.median(relative[first])),
            "first_quarter_label0_median_peak_value_native": first_peak,
            "last_quarter_label0_median_peak_value_native": last_peak,
            "peak_median_change_percent": 100.0 * (last_peak / first_peak - 1.0),
            "first_quarter_label0_median_peak_index": float(np.median(peak_index[first])),
            "last_quarter_label0_median_peak_index": float(np.median(peak_index[last])),
        })
        provenance.append({
            "sequence_id": sequence_id, "filename": filename, "wire_gauge_awg": gauge,
            "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_records": n, "n_label0": int(accepted.sum()),
            "n_label1": int((labels == 1).sum()),
            "reference_record_id": reference_id,
            "reference_l1_norm_native": denominator,
            "quarter_boundaries_zero_based_half_open": boundaries,
        })
        plotted.append((sequence_id, filename, gauge, labels, relative, rolling))

    assert len(all_records) == 9829
    assert sum(r["label"] == 0 for r in all_records) == 9803
    assert sum(r["label"] == 1 for r in all_records) == 26
    write_csv(args.summary_dir / "per_record_drift_descriptors.csv", all_records)
    write_csv(args.summary_dir / "drift_summary.csv", summaries)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": .65, "savefig.dpi": 320,
        "svg.fonttype": "none", "pdf.fonttype": 42,
    })
    fig, axs = plt.subplots(3, 2, figsize=(7.3, 6.2))
    for i, (ax, (sequence_id, filename, gauge, labels, relative, rolling)) in enumerate(zip(axs.flat, plotted)):
        rows = np.arange(1, len(relative) + 1)
        accepted = labels == 0
        ax.scatter(rows[accepted], relative[accepted], s=3.0, marker=".",
                   color="#245D83", alpha=.45, linewidths=0,
                   label="Normal operations", zorder=2)
        ax.plot(rows, rolling, color="#AD5E1D", lw=1.2,
                label="Trailing median (100 retained rows)", zorder=3)
        ax.set_title(f"{chr(97 + i)}   {FILE_DATE_LABELS[filename]}   {gauge} AWG", loc="left",
                     fontsize=9.5, weight="bold")
        ax.set_xlim(1, len(relative))
        ax.set_ylim(0, max(float(relative[accepted].max()) * 1.07, .1))
        ax.set_ylabel("Relative L1 distance (%)", fontsize=8.5)
        if i >= 4:
            ax.set_xlabel("Retained operation index", fontsize=8.5)
        ax.grid(alpha=.17, linewidth=.55)
        ax.tick_params(labelsize=8, pad=2)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    handles, labels = axs.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .002),
               ncol=2, frameon=False, fontsize=8, markerscale=2)
    fig.tight_layout(rect=(0, .052, 1, 1), h_pad=1.25, w_pad=1.4)
    for extension in ["png", "svg"]:
        fig.savefig(args.output_dir / f"figure4_gauge_drift.{extension}")
    plt.close(fig)

    methods = {
        "analysis": "Descriptive distance from each sequence's initial accepted waveform",
        "formula": "relative_L1_i_percent = 100 * sum_j(abs(x_ij - x_ref_j)) / sum_j(abs(x_ref_j)), j=1..200",
        "l1_distance_native": "sum_j(abs(x_ij - x_ref_j)); native export scale summed over 200 points",
        "reference": "First record with label 0 in the same file; fixed throughout that file. The reference is a measured waveform, not the instrument's exported reference row.",
        "normalization": "One denominator per file: L1 norm of that file's first label-0 waveform. No centering, per-record amplitude scaling, alignment, waveform smoothing or resampling.",
        "descriptor_population": "All 9,829 records, including both CFM classes",
        "scatter_population": "Only 9,803 CFM-accepted (label 0) records; all 26 label-1 records are excluded from scatter and trailing medians",
        "row_index": "One-based data-row position in each retained CSV, excluding the header. Rejected positions are not removed or reindexed.",
        "trailing_median": {
            "window": "At one-based row i, use retained positions max(1,i-99)..i inclusive; keep only label-0 records within these positions",
            "window_width_retained_row_positions": 100,
            "min_accepted_observations": 1,
            "evaluation_positions": "Every retained row position, including label-1 positions; the current row contributes only when label 0",
            "empty_window": "Undefined (blank CSV / NaN line break); no empty window occurs in these six files",
            "future_data": "None; the median is trailing, not centered",
            "role": "Visualization summary only; not a fitted drift detector or CFM decision rule",
        },
        "quarter_summary": {
            "boundaries": "b_k=floor(k*n/4), k=0..4, on all retained records. First quarter is zero-based [b_0,b_1); last is [b_3,b_4). Filter label 0 after selecting these intervals.",
            "statistics": "Separate medians of relative L1 percent, waveform maximum and first maximum point index among label-0 records in each interval",
            "peak_index": "One-based first occurrence of the maximum within the 200-point vector",
            "peak_change_percent": "100*(last_quarter_median_peak/first_quarter_median_peak - 1)",
            "relative_l1_change": "Last-quarter minus first-quarter median relative L1, in percentage points",
        },
        "gauge_provenance": "Author-confirmed wire-gauge mapping; gauge is not inferred from signal amplitude or filename",
        "visible_labels": {"date": "Filename identifiers; not independently verified acquisition dates", "normal": "Operational CFM label 0", "display_dates": FILE_DATE_LABELS},
        "figure": {"layout": "3 rows x 2 columns, A-F in row-major order", "size_inches": [7.3, 6.2], "dpi": 320, "vertical_scale": "Separate linear ranges per panel, each including zero and every accepted distance"},
        "interpretation": "Observed distance variation is descriptive. No drift-onset ground truth, causal mechanism, gauge-only effect or machine-learning performance is inferred.",
        "validation": {"records": len(all_records), "waveform_values": len(all_records) * 200, "label0": 9803, "label1": 26, "finite_signal_values": True, "finite_distances": True, "reference_distance_zero": True, "record_order_preserved": True},
        "files": provenance,
    }
    (args.summary_dir / "drift_methods.json").write_text(
        json.dumps(methods, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in summaries:
        print(f"{row['sequence_id']} {row['wire_gauge_awg']} AWG: Q1/Q4 relative L1 "
              f"{row['first_quarter_label0_median_relative_l1_percent']:.4f}% / "
              f"{row['last_quarter_label0_median_relative_l1_percent']:.4f}%; "
              f"median peak change {row['peak_median_change_percent']:+.4f}%")
    print("Validated 9,829 records (9,803 accepted; 26 rejected); saved Figure 4, descriptors, summary and methods.")


if __name__ == "__main__":
    main()
