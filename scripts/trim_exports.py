"""Safe command-line adaptation of the supplied historical trimming logic.

Applies forward-fill to all imported columns, assigns pair labels using the
historical counter branch order, removes Unknown pairs, and exports 200 waveform
columns plus Results. It does not select the final six production segments.
No output cleanup is performed. The output folder must be new.
"""
import argparse
from pathlib import Path
import pandas as pd
from validate_source_correspondence import read_export, counter_labels


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():parser.error('Use a new output directory; no existing files are deleted.')
    paths=sorted(args.source_dir.glob('*.csv'))
    if not paths:parser.error('No CSV exports found.')
    results=[]
    for path in paths:
        header,rows,first=read_export(path)
        labels=counter_labels(header,rows)
        original=pd.read_csv(path,skiprows=1)
        if len(original)!=len(rows):raise ValueError(f'Row count mismatch: {path.name}')
        filled=original.ffill()
        pair_labels=[v for lab in labels for v in
                     ((('g1','g2') if lab=='g2' else ('b1','b2')) if lab!='Unknown' else ('Unknown','Unknown'))]
        frame=filled.iloc[:,first:first+200].copy()
        frame.columns=[f'data{i}' for i in range(1,201)]
        frame['Results']=pair_labels
        frame=frame[frame['Results']!='Unknown']
        results.append((path.stem+'_trimming.csv',frame))
    args.output_dir.mkdir(parents=True)
    for name,frame in results:frame.to_csv(args.output_dir/name,index=False)
    print(f'Trimmed {len(results)} exports. Final production-segment selection is a separate step.')


if __name__=='__main__':main()
