"""Reconstruct the six retained CSVs from supplied exports and the published row map.

This is a mapped reconstruction, not recovery of historical selection decisions.
Input files are read only. The output directory must not already exist.
"""
import argparse
import csv
import math
from pathlib import Path
from validate_source_correspondence import read_export, counter_labels, numeric


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,action='append',required=True)
    parser.add_argument('--map',type=Path,default=root/'metadata/record_correspondence.csv')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Choose a new output directory; existing files will not be overwritten.')
    with args.map.open(encoding='utf-8-sig',newline='') as f:
        mapping=list(csv.DictReader(f))
    sources={}
    for name in {m['source_filename'] for m in mapping}:
        paths=[p/name for p in args.source_dir if (p/name).is_file()]
        if len(paths)!=1:raise ValueError(f'Need exactly one source named {name}')
        h,rows,first=read_export(paths[0])
        sources[name]=(rows,first,counter_labels(h,rows))
    outputs={}
    for m in mapping:
        rows,first,labels=sources[m['source_filename']]
        i=int(m['source_data_record_one_based'])-1
        if i%2!=1:raise ValueError('Mapping must refer to measurement rows.')
        values=rows[i][first:first+200]
        if len(values)!=200 or not all(math.isfinite(numeric(v)) for v in values):
            raise ValueError('Missing/non-finite waveform value; no forward-fill is allowed for retained values.')
        label={'g2':0,'b2':1}.get(labels[i//2])
        if label is None or label!=int(m['label']):raise ValueError('Mapped counter label mismatch.')
        bucket=outputs.setdefault(m['filename'],{})
        pos=int(m['row_index'])
        if pos in bucket:raise ValueError('Duplicate retained row position.')
        bucket[pos]=values+[str(label)]
    for name,rows in outputs.items():
        if set(rows)!=set(range(1,len(rows)+1)):raise ValueError(f'Incomplete row range in {name}')
    if sum(map(len,outputs.values()))!=9829:raise ValueError('Expected 9,829 retained records.')
    args.output_dir.mkdir(parents=True)
    for name,rows in outputs.items():
        with (args.output_dir/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow([f'data{i}' for i in range(1,201)]+['label'])
            w.writerows(rows[i] for i in range(1,len(rows)+1))
    print('Reconstructed 9,829 retained records from the map. Compare numeric values, not CSV byte formatting.')


if __name__=='__main__':main()
