"""Validate included CSVs; source verification is opt-in and reported separately."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, action='append', default=[],
                        help='Folder of authorized source exports; repeat if needed.')
    args = parser.parse_args()
    manifest = json.loads((root/'metadata/data_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        actual = hashlib.sha256((root/'data'/item['filename']).read_bytes()).hexdigest()
        require(actual == item['sha256'], f"Data checksum mismatch: {item['filename']}")
    snapshot = root/'metadata/package_manifest.json'
    if snapshot.exists():
        for item in json.loads(snapshot.read_text(encoding='utf-8'))['files']:
            path = root/item['path']
            require(path.is_file(), f"Missing package file: {item['path']}")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'],
                    f"Package checksum mismatch: {item['path']}; regenerate the manifest after intentional edits.")
    with (root/'metadata/record_correspondence.csv').open(encoding='utf-8-sig', newline='') as f:
        mapping = list(csv.DictReader(f))
    expected = {(item['filename'], i) for item in manifest['files'] for i in range(1,item['records']+1)}
    keys = [(m['filename'], int(m['row_index'])) for m in mapping]
    require(len(keys) == len(set(keys)) == 9829 and set(keys) == expected,
            'The correspondence table must cover every retained row exactly once.')
    for item in manifest['files']:
        with (root/'data'/item['filename']).open(encoding='utf-8-sig', newline='') as f:
            records=list(csv.DictReader(f))
        mapped=[m for m in mapping if m['filename']==item['filename']]
        require(all(int(m['label']) == int(float(records[int(m['row_index'])-1]['label'])) for m in mapped),
                'Correspondence-table label mismatch.')
        positions=[int(m['source_data_record_one_based']) for m in mapped]
        require(all(a < b for a,b in zip(positions,positions[1:])), 'Non-increasing mapped source order.')
    out = root/'validation/rerun'
    subprocess.run([sys.executable, str(root/'scripts/validate_release.py'),
                    '--input-dir', str(root/'data'), '--output-dir', str(out)], check=True)
    release=json.loads((out/'release_validation.json').read_text(encoding='utf-8'))
    require(release['totals']['rows']==9829 and release['totals']['label_counts']=={'0':9803,'1':26},
            'Unexpected class counts.')
    status={'public_data_checks':'passed','records':9829,'signal_values':1965800,
            'normal':9803,'abnormal':26,'mapping_coverage':'9829 unique retained rows',
            'source_matching':'not_run','source_matching_reason':'No source exports supplied.'}
    if args.source_dir:
        cmd=[sys.executable,str(root/'scripts/validate_source_correspondence.py'),
             '--data-dir',str(root/'data'),'--output',str(out/'source_validation_report.json')]
        for folder in args.source_dir:
            cmd.extend(['--source-dir',str(folder)])
        subprocess.run(cmd,check=True)
        source=json.loads((out/'source_validation_report.json').read_text(encoding='utf-8'))
        require(source['checks']['records_checked']==9829 and source['checks']['values_checked']==1965800,
                'Incomplete source check.')
        status.update(source_matching='passed_against_supplied_files', source_matching_reason=None)
    (out/'check_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2))


if __name__ == '__main__':
    main()
