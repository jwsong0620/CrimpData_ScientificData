"""Check the prepared record map against supplied original Pro-Lite exports.

Requires Python 3.10+ standard library. Inputs are read only. The original
trimming script is neither executed nor imported. This reconstructs checks,
not the unpreserved historical selection procedure.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def read_export(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        preamble = next(reader)
        header = next(reader)
        rows = list(reader)
    assert len(rows) % 2 == 0, f'Odd paired-row count: {path.name}'
    first = next(i for i, name in enumerate(header) if 'ForceCurve(' in name)
    return header, rows, first


def numeric(value):
    return float(value) if value.strip() else float('nan')


def counter_labels(header, rows):
    """Literal branch order reconstructed from the supplied trimming script."""
    good_idx, bad_idx = header.index('Good'), header.index('Bad')
    good = [numeric(row[good_idx]) for row in rows[::2]]
    bad = [numeric(row[bad_idx]) for row in rows[::2]]
    previous_good = previous_bad = 0.0
    result = []
    for i, (current_good, current_bad) in enumerate(zip(good, bad)):
        next_good = good[i + 1] if i + 1 < len(good) else None
        next_bad = bad[i + 1] if i + 1 < len(bad) else None
        boundary = (next_good == 0 and next_bad == 0) or (next_good is None and next_bad is None)
        label = 'Unknown'
        if current_good == 0 and current_bad == 0:
            previous_good = previous_bad = 0.0
        elif i == 0 and (current_good != 0 or current_bad != 0):
            previous_good, previous_bad = current_good, current_bad
        elif i > 0 and current_good - previous_good == 1:
            label = 'Unknown' if boundary else 'g2'
            previous_good = current_good
        elif i > 0 and current_bad - previous_bad == 1:
            label = 'Unknown' if boundary else 'b2'
            previous_bad = current_bad
        result.append(label)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--source-dir', type=Path, action='append', required=True,
                        help='Directory containing original exports; repeat for multiple directories.')
    parser.add_argument('--map', type=Path, default=Path(__file__).resolve().parents[1] / 'metadata' / 'record_correspondence.csv')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.map.open(encoding='utf-8-sig', newline='') as stream:
        mapping = list(csv.DictReader(stream))
    source_names = {row['source_filename'] for row in mapping}
    sources = {}
    for name in source_names:
        candidates = [base / name for base in args.source_dir if (base / name).is_file()]
        assert len(candidates) == 1, f'Provide exactly one original export named {name}'
        path = candidates[0]
        header, rows, first = read_export(path)
        sources[name] = (header, rows, first, counter_labels(header, rows), path)
    final = {}
    for name in {row['filename'] for row in mapping}:
        with (args.data_dir / name).open(encoding='utf-8-sig', newline='') as stream:
            final[name] = list(csv.DictReader(stream))
    checks = {'records_checked': 0, 'values_checked': 0, 'missing_or_nonfinite_source_values': 0,
              'waveform_mismatches': 0, 'label_mismatches': 0, 'metadata_mismatches': 0,
              'source_order_violations': 0, 'maximum_absolute_difference': 0.0}
    previous_positions = {}
    for item in mapping:
        header, rows, first, labels, path = sources[item['source_filename']]
        row_index = int(item['row_index']) - 1
        source_index = int(item['source_data_record_one_based']) - 1
        assert source_index % 2 == 1, 'Map must identify the lower measurement row.'
        assert int(item['source_csv_line_one_based']) == source_index + 3
        assert int(item['metadata_csv_line_one_based']) == source_index + 2
        original_values = [numeric(value) for value in rows[source_index][first:first+200]]
        retained = final[item['filename']][row_index]
        retained_values = [float(retained[f'data{i}']) for i in range(1,201)]
        assert len(original_values) == 200
        missing = sum(not math.isfinite(value) for value in original_values)
        checks['missing_or_nonfinite_source_values'] += missing
        checks['waveform_mismatches'] += original_values != retained_values
        if not missing:
            difference = max(abs(a-b) for a,b in zip(original_values,retained_values))
            checks['maximum_absolute_difference'] = max(checks['maximum_absolute_difference'], difference)
        reconstructed = labels[source_index // 2]
        expected = {'g2': 0, 'b2': 1}.get(reconstructed)
        checks['label_mismatches'] += expected != int(retained['label'])
        for map_key, source_key in [('timestamp','Date/Time'), ('good_counter','Good'), ('bad_counter','Bad')]:
            checks['metadata_mismatches'] += item[map_key] != rows[source_index-1][header.index(source_key)]
        prior = previous_positions.get(item['filename'])
        checks['source_order_violations'] += prior is not None and source_index <= prior
        previous_positions[item['filename']] = source_index
        checks['records_checked'] += 1
        checks['values_checked'] += 200
    result = {'checks':checks, 'source_files':[{'filename':name,'sha256':hashlib.sha256(data[-1].read_bytes()).hexdigest()} for name,data in sorted(sources.items())],
              'interpretation':'Checks correspondence at supplied mapped positions and reconstructed CFM-counter agreement. It does not recover selection reasons, certify physical defect truth, or independently search every potential source file.'}
    # Refuse to overwrite any measurement or mapping input.
    protected = {path.resolve() for *_,path in sources.values()} | {args.map.resolve()}
    protected |= {(args.data_dir / name).resolve() for name in final}
    assert args.output.resolve() not in protected
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))
    failures = sum(checks[k] for k in ('missing_or_nonfinite_source_values','waveform_mismatches','label_mismatches','metadata_mismatches','source_order_violations'))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
