#!/usr/bin/env python3
"""Read-only structural and descriptive checks for the six crimping CSV files.

Python 3.9+; standard library only. Does not change the input files or train a model.
Example:
    python validate_release.py --input-dir path/to/content/data --output-dir validation

The six filenames are release identifiers, not an assertion of acquisition dates.
Signal values remain on the native export scale. Point positions are 1-based indices,
not physical time. No calibration or saturation threshold is assumed.
"""

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import statistics
import struct
from collections import Counter, defaultdict


FILES = (
    '20230426.csv', '20230427.csv', '20230428.csv',
    '20230503.csv', '20230504.csv', '20230505.csv',
)
POINTS = 200
HEADER = [f'data{i}' for i in range(1, POINTS + 1)] + ['label']
DESCRIPTOR_FIELDS = [
    'record_id', 'sequence_id', 'filename', 'row_index', 'label',
    'peak_value', 'peak_index', 'trailing_zero_count', 'all_zero', 'constant',
    'first_nonzero_index', 'last_nonzero_index', 'leading_zero_count',
    'zero_count', 'interior_zero_count', 'minimum_value', 'rms_value',
    'mean_to_peak_ratio', 'points_at_or_above_half_peak',
    'peak_tie_count', 'longest_run_at_peak',
]
SUMMARY_METRICS = [
    'peak_value', 'peak_index', 'first_nonzero_index', 'last_nonzero_index',
    'leading_zero_count', 'trailing_zero_count', 'zero_count',
    'interior_zero_count', 'rms_value', 'mean_to_peak_ratio',
    'points_at_or_above_half_peak', 'peak_tie_count', 'longest_run_at_peak',
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def quantile(sorted_values, probability):
    """Linear interpolation at (n-1)*q; same convention as numpy method='linear'."""
    position = (len(sorted_values) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def summary(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {'n': 0, 'minimum': None, 'q05': None, 'q25': None,
                'median': None, 'q75': None, 'q95': None, 'maximum': None}
    return {
        'n': len(vals), 'minimum': vals[0], 'q05': quantile(vals, .05),
        'q25': quantile(vals, .25), 'median': quantile(vals, .5),
        'q75': quantile(vals, .75), 'q95': quantile(vals, .95), 'maximum': vals[-1],
    }


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def describe_waveform(wave, sequence_id, filename, row_index, label):
    maximum = max(wave)
    minimum = min(wave)
    nonzero = [i for i, value in enumerate(wave) if value != 0]
    first = nonzero[0] + 1 if nonzero else None
    last = nonzero[-1] + 1 if nonzero else None
    leading = first - 1 if first is not None else POINTS
    trailing = POINTS - last if last is not None else POINTS
    zeros = sum(value == 0 for value in wave)
    interior = zeros - leading - trailing if nonzero else 0
    longest = run = 0
    for value in wave:
        run = run + 1 if value == maximum else 0
        longest = max(longest, run)
    return {
        'record_id': f'{filename}:{row_index}', 'sequence_id': sequence_id,
        'filename': filename, 'row_index': row_index, 'label': label,
        'peak_value': maximum, 'peak_index': wave.index(maximum) + 1,
        'trailing_zero_count': trailing, 'all_zero': int(not nonzero),
        'constant': int(minimum == maximum), 'first_nonzero_index': first,
        'last_nonzero_index': last, 'leading_zero_count': leading,
        'zero_count': zeros, 'interior_zero_count': interior,
        'minimum_value': minimum,
        'rms_value': math.sqrt(math.fsum(value * value for value in wave) / POINTS),
        'mean_to_peak_ratio': (math.fsum(wave) / (POINTS * maximum)) if maximum > 0 else None,
        'points_at_or_above_half_peak': sum(value >= maximum / 2 for value in wave) if maximum > 0 else None,
        'peak_tie_count': sum(value == maximum for value in wave),
        'longest_run_at_peak': longest,
    }


def group_summary(records):
    return {
        'rows': len(records),
        'rows_with_trailing_zeros': sum(r['trailing_zero_count'] > 0 for r in records),
        'rows_with_interior_zeros': sum(r['interior_zero_count'] > 0 for r in records),
        'rows_with_peak_ties': sum(r['peak_tie_count'] > 1 for r in records),
        'rows_with_at_least_three_consecutive_peak_values': sum(r['longest_run_at_peak'] >= 3 for r in records),
        'metrics': {key: summary(r[key] for r in records) for key in SUMMARY_METRICS},
        'trailing_zero_count_distribution': histogram(r['trailing_zero_count'] for r in records),
    }


def parse_file(path, sequence_id):
    raw = path.read_bytes()
    reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    header = next(reader, None)
    if header != HEADER:
        raise ValueError(f'{path.name}: expected ordered data1..data200,label header')
    waves = []
    records = []
    canonical = hashlib.sha256()
    for row_index, cells in enumerate(reader, 1):
        if len(cells) != POINTS + 1:
            raise ValueError(f'{path.name}:{row_index}: {len(cells)} cells; expected 201')
        if any(not cell.strip() for cell in cells):
            raise ValueError(f'{path.name}:{row_index}: empty cell')
        try:
            wave = tuple(float(value) for value in cells[:POINTS])
            numeric_label = float(cells[-1])
        except ValueError as exc:
            raise ValueError(f'{path.name}:{row_index}: nonnumeric cell') from exc
        if not all(math.isfinite(value) for value in wave):
            raise ValueError(f'{path.name}:{row_index}: nonfinite signal value')
        if numeric_label not in (0, 1):
            raise ValueError(f'{path.name}:{row_index}: label must be 0 or 1')
        # Canonical numeric hash uses 200 little-endian float64 values plus one
        # unsigned label byte per row. Normalize signed zero. Preserve row order.
        wave = tuple(0.0 if value == 0 else value for value in wave)
        label = int(numeric_label)
        canonical.update(struct.pack('<200dB', *wave, label))
        waves.append(wave)
        records.append(describe_waveform(wave, sequence_id, path.name, row_index, label))
    if not waves:
        raise ValueError(f'{path.name}: empty dataset')
    counts = Counter(r['label'] for r in records)
    maximum = max(r['peak_value'] for r in records)
    constant_columns = [i + 1 for i in range(POINTS) if all(row[i] == waves[0][i] for row in waves)]
    report = {
        'sequence_id': sequence_id, 'filename': path.name,
        'bytes': len(raw), 'sha256': digest(raw),
        'sha256_after_crlf_to_lf': digest(raw.replace(b'\r\n', b'\n')),
        'canonical_numeric_records_sha256': canonical.hexdigest(),
        'header': header, 'data_rows': len(waves), 'waveform_columns': POINTS,
        'label_counts': {str(label): counts[label] for label in (0, 1)},
        'missing_values': 0, 'nonnumeric_values': 0, 'nonfinite_values': 0,
        'signal_value_count': len(waves) * POINTS,
        'negative_values': sum(value < 0 for row in waves for value in row),
        'noninteger_values': sum(not value.is_integer() for row in waves for value in row),
        'minimum_stored_value': min(r['minimum_value'] for r in records),
        'maximum_stored_value': maximum,
        'zero_values': sum(r['zero_count'] for r in records),
        'all_zero_rows': sum(r['all_zero'] for r in records),
        'constant_rows': sum(r['constant'] for r in records),
        'constant_columns': constant_columns,
        'rows_reaching_file_maximum': sum(r['peak_value'] == maximum for r in records),
        'cells_at_file_maximum': sum(value == maximum for row in waves for value in row),
        'all_records': group_summary(records),
        'by_label': {str(label): group_summary([r for r in records if r['label'] == label]) for label in (0, 1)},
    }
    return raw, waves, records, report


def format_interval(stats, decimals=1):
    if stats['n'] == 0:
        return 'NA'
    return f"{stats['median']:.{decimals}f} [{stats['q25']:.{decimals}f}, {stats['q75']:.{decimals}f}]"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True, help='Directory containing the six original release CSVs')
    parser.add_argument('--output-dir', type=Path, required=True, help='Separate directory for JSON, CSV and TXT validation results')
    args = parser.parse_args()
    src = args.input_dir.resolve()
    dest = args.output_dir.resolve()
    if src == dest:
        parser.error('Use a separate output directory to keep source records unchanged.')
    all_records = []
    file_reports = []
    initial_hashes = {}
    duplicate_map = defaultdict(list)
    pointwise = []
    for sequence_id, filename in zip('ABCDEF', FILES):
        raw, waves, records, result = parse_file(src / filename, sequence_id)
        initial_hashes[filename] = digest(raw)
        file_reports.append(result)
        all_records.extend(records)
        for wave, record in zip(waves, records):
            duplicate_map[wave].append((record['record_id'], record['label']))
        label0 = [wave for wave, record in zip(waves, records) if record['label'] == 0]
        for index in range(POINTS):
            stat = summary(wave[index] for wave in label0)
            pointwise.append({'sequence_id': sequence_id, 'filename': filename, 'label': 0,
                              'point_index': index + 1, 'n': len(label0),
                              'q05': stat['q05'], 'median': stat['median'], 'q95': stat['q95']})
    duplicates = [{'record_ids': [r[0] for r in group], 'labels': [r[1] for r in group]}
                  for group in duplicate_map.values() if len(group) > 1]
    final_hashes = {name: digest((src / name).read_bytes()) for name in FILES}
    if initial_hashes != final_hashes:
        raise RuntimeError('An input changed during the audit; results were not written.')
    totals = {
        'files': len(file_reports), 'rows': len(all_records),
        'signal_values': len(all_records) * POINTS,
        'label_counts': {str(label): sum(r['label'] == label for r in all_records) for label in (0, 1)},
        'minimum_stored_value': min(r['minimum_value'] for r in all_records),
        'maximum_stored_value': max(r['peak_value'] for r in all_records),
        'negative_values': sum(r['negative_values'] for r in file_reports),
        'noninteger_values': sum(r['noninteger_values'] for r in file_reports),
        'zero_values': sum(r['zero_count'] for r in all_records),
        'all_zero_rows': sum(r['all_zero'] for r in all_records),
        'constant_rows': sum(r['constant'] for r in all_records),
        'rows_with_trailing_zeros': sum(r['trailing_zero_count'] > 0 for r in all_records),
        'rows_with_interior_zeros': sum(r['interior_zero_count'] > 0 for r in all_records),
        'exact_duplicate_extra_rows': sum(len(group['record_ids']) - 1 for group in duplicates),
        'exact_duplicate_label_conflict_groups': sum(len(set(group['labels'])) > 1 for group in duplicates),
        'summary': group_summary(all_records),
    }
    report = {
        'schema_version': '1.0', 'python_version': platform.python_version(),
        'script_sha256': digest(Path(__file__).read_bytes()),
        'read_only_input_hash_check_passed': initial_hashes == final_hashes,
        'methods': {
            'scope': 'Six released CSVs only. No classifier training, raw-export matching, calibration, or physical product inspection is performed by this script.',
            'schema': 'UTF-8 CSV, one header row, ordered data1..data200,label; finite numeric signal values and label 0/1 are required. Failure stops before results are written.',
            'quantiles': 'Linear interpolation at (n-1)*q; min, 5th, 25th, 50th, 75th, 95th, max percentiles. These describe the retained records, not sampling uncertainty.',
            'peak': 'Largest stored value. Peak index is the first index attaining that value, with indices 1..200.',
            'zero_boundaries': 'Exact numeric zero. First/last nonzero indices are 1-based; null for an all-zero row. All-zero rows have 200 leading and 200 trailing zeros by convention and zero interior zeros.',
            'shape': 'Mean-to-peak ratio = sum(x)/(200*max(x)); half-peak count = number of points x>=0.5*max(x). They are descriptive index-domain features, not energy, work or duration. Null if peak<=0.',
            'rms': 'sqrt(sum(x*x)/200), on native export scale; no physical calibration inferred.',
            'peak_ties': 'Count exact occurrences of the row maximum and longest consecutive run at that maximum. Quantization or plateau evidence alone cannot establish instrument saturation.',
            'duplicates': 'Exact equality of complete 200-value Python float tuples; labels are excluded from waveform identity.',
            'canonical_hash': 'Concatenate each row as 200 little-endian float64 values with signed zero normalized, followed by one unsigned label byte. This hash scheme differs from earlier textual canonical hashes.',
            'pointwise_summary': 'The optional companion CSV contains the label-0 pointwise median and 5th/95th percentiles, without smoothing, alignment, resampling or normalization.',
        },
        'files': file_reports, 'totals': totals, 'duplicate_groups': duplicates,
        'saturation_assessment': {
            'status': 'not established',
            'reason': 'ADC resolution, transfer function, full-scale and saturation flags are not supplied. Observed maxima and flat-top counts are descriptive and cannot demonstrate either saturation or its absence.',
        },
    }
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'release_validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    with (dest / 'per_record_descriptors.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=DESCRIPTOR_FIELDS)
        writer.writeheader(); writer.writerows(all_records)
    with (dest / 'label0_pointwise_summary.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pointwise[0]))
        writer.writeheader(); writer.writerows(pointwise)
    compact_fields = ['sequence_id', 'filename', 'records', 'label0', 'label1', 'range_min', 'range_max',
                      'all_zero_rows', 'constant_rows', 'rows_with_zero_tail',
                      'label0_peak_median', 'label0_peak_q25', 'label0_peak_q75',
                      'label0_peak_index_median', 'label0_peak_index_q25', 'label0_peak_index_q75',
                      'label0_mean_to_peak_median', 'label0_half_peak_count_median']
    compact_rows = []
    text = ['Descriptive validation of the six released crimping waveform files', '',
            'Values use the native export scale; index positions are 1-based, not time.',
            'Intervals below are medians [25th, 75th percentile] of label-0 records.', '',
            'Sequence | filename | n(0/1) | value range | zero-tail rows | label-0 peak | peak index | mean/peak | half-peak points']
    for r in file_reports:
        m = r['by_label']['0']['metrics']
        text.append(f"{r['sequence_id']} | {r['filename']} | {r['data_rows']} ({r['label_counts']['0']}/{r['label_counts']['1']}) | {r['minimum_stored_value']:g}..{r['maximum_stored_value']:g} | {r['all_records']['rows_with_trailing_zeros']} | {format_interval(m['peak_value'])} | {format_interval(m['peak_index'])} | {format_interval(m['mean_to_peak_ratio'], 4)} | {format_interval(m['points_at_or_above_half_peak'])}")
        compact_rows.append({
            'sequence_id': r['sequence_id'], 'filename': r['filename'], 'records': r['data_rows'],
            'label0': r['label_counts']['0'], 'label1': r['label_counts']['1'],
            'range_min': r['minimum_stored_value'], 'range_max': r['maximum_stored_value'],
            'all_zero_rows': r['all_zero_rows'], 'constant_rows': r['constant_rows'],
            'rows_with_zero_tail': r['all_records']['rows_with_trailing_zeros'],
            'label0_peak_median': m['peak_value']['median'], 'label0_peak_q25': m['peak_value']['q25'], 'label0_peak_q75': m['peak_value']['q75'],
            'label0_peak_index_median': m['peak_index']['median'], 'label0_peak_index_q25': m['peak_index']['q25'], 'label0_peak_index_q75': m['peak_index']['q75'],
            'label0_mean_to_peak_median': m['mean_to_peak_ratio']['median'], 'label0_half_peak_count_median': m['points_at_or_above_half_peak']['median'],
        })
    text += ['', f"Total: {totals['rows']} records; {totals['signal_values']} finite values; labels {totals['label_counts']}.",
             f"Noninteger values: {totals['noninteger_values']}; negative values: {totals['negative_values']}; all-zero rows: {totals['all_zero_rows']}; constant rows: {totals['constant_rows']}.",
             f"Trailing-zero rows: {totals['rows_with_trailing_zeros']}; exact duplicate extra rows: {totals['exact_duplicate_extra_rows']}.",
             'Saturation is not established: ADC range, calibration and saturation flags are unavailable.',
             'Peak ties and zero portions are retained observations, not proof of clipping, padding or a defect mechanism.',
             'Descriptive differences between sequence_ids do not identify their physical cause or imply a production-wide defect rate.',
             'Input SHA-256 hashes were unchanged after the read-only audit.', '']
    (dest / 'release_validation_table.txt').write_text('\n'.join(text), encoding='utf-8')
    with (dest / 'release_validation_table.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=compact_fields)
        writer.writeheader(); writer.writerows(compact_rows)
    print(json.dumps({'rows': totals['rows'], 'signal_values': totals['signal_values'],
                      'all_zero_rows': totals['all_zero_rows'], 'constant_rows': totals['constant_rows'],
                      'rows_with_trailing_zeros': totals['rows_with_trailing_zeros'],
                      'exact_duplicate_extra_rows': totals['exact_duplicate_extra_rows'],
                      'output_directory': str(dest)}, indent=2))


if __name__ == '__main__':
    main()
