"""Reproduce manuscript Figure 3 from released CSVs; Figure 2 also requires the source export.
Dependencies: numpy, pandas and matplotlib. This is documentation/plotting code,
not the historical data selection script. Source files are never modified.
"""
from pathlib import Path
import argparse, csv, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import numpy as np
import pandas as pd

parser=argparse.ArgumentParser(description="Reproduce waveform overview and paired-reference figures from the six released CSVs.")
parser.add_argument('--input-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--source-dir',type=Path,action='append',default=[])
parser.add_argument('--map',type=Path,default=Path(__file__).resolve().parents[1] / 'metadata' / 'record_correspondence.csv')
args=parser.parse_args()
out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
filenames=['20230426.csv','20230427.csv','20230428.csv','20230503.csv','20230504.csv','20230505.csv']
gauge_by_file=dict(zip(filenames,[18,16,18,20,14,22]))
# Display dates identify filenames; they are not verified acquisition timestamps.
date_by_file=dict(zip(filenames,['26 Apr 2023','27 Apr 2023','28 Apr 2023','3 May 2023','4 May 2023','5 May 2023']))
files=[{'filename':name,'wire_gauge_awg':gauge_by_file[name],'display_date':date_by_file[name]} for name in filenames]
datasets=[pd.read_csv(args.input_dir/name) for name in filenames]
with args.map.open(encoding='utf-8-sig',newline='') as stream:
 correspondence=list(csv.DictReader(stream))
example_info=[]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'savefig.dpi':320,'pdf.fonttype':42,'svg.fonttype':'none'})
blue='#245D83';red='#B74539';light='#DCEAF2'

x=np.arange(1,201)
if args.source_dir:
 df=datasets[0]
 fig,axs=plt.subplots(1,2,figsize=(7.3,3.35),sharex=True)
 example_info=[]
 for ax,lab,letter in zip(axs,[0,1],['a','b']):
  idx=int(np.flatnonzero(df['label'].to_numpy()==lab)[0])
  match=next(m for m in correspondence if m['filename']==filenames[0] and int(m['row_index'])==idx+1)
  paths=[folder/match['source_filename'] for folder in args.source_dir if (folder/match['source_filename']).is_file()]
  assert len(paths)==1, 'Supply exactly one matching original export.'
  raw=pd.read_csv(paths[0],skiprows=1)
  c0=next(i for i,c in enumerate(raw.columns) if 'ForceCurve(' in c)
  ri=int(match['source_data_record_one_based'])-1
  ref=raw.iloc[ri-1,c0:c0+200].to_numpy(dtype=float);meas=raw.iloc[ri,c0:c0+200].to_numpy(dtype=float)
  assert np.array_equal(meas,df.iloc[idx,:200].to_numpy(dtype=float))
  ax.plot(x,ref,color='#82888C',linestyle='--',lw=1.4,label='Exported reference')
  ax.plot(x,meas,color=blue if lab==0 else red,lw=1.4,label='Normal' if lab==0 else 'Abnormal')
  ax.set_title(f'{letter}   {date_by_file[filenames[0]]}   18 AWG\n{"Normal" if lab==0 else "Abnormal"}',loc='left',fontsize=9.5,weight='bold')
  ax.set_xlabel('Within-operation point index');ax.set_ylabel('Signal (native export scale)');ax.set_xlim(1,200);ax.grid(alpha=.18)
  ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
  example_info.append({'label':lab,'final_row_one_based':idx+1,'source_filename':match['source_filename'],'source_csv_line_one_based':int(match['source_csv_line_one_based'])})
 for ax in axs:ax.legend(loc='upper left',fontsize=8,frameon=False)
 fig.tight_layout(pad=.6,w_pad=1.6);fig.savefig(out/'figure2_export_pair.png');fig.savefig(out/'figure2_export_pair.svg');plt.close(fig)

else:
 print('Figure 2 requires the original source export; provide --source-dir.')

fig,axs=plt.subplots(3,2,figsize=(7.3,7.4),sharex=True)
for ax,df,f,letter,panel in zip(axs.flat,datasets,files,'ABCDEF','abcdef'):
 X=df.iloc[:,:200].to_numpy(dtype=float);y=df['label'].to_numpy();normal=X[y==0]
 q=np.quantile(normal,[.05,.5,.95],axis=0)
 ax.fill_between(x,q[0],q[2],color=blue,alpha=.18,linewidth=0,label='Normal  5th–95th percentiles')
 ax.plot(x,q[1],color=blue,lw=1.25,label='Normal  median')
 for i,curve in enumerate(X[y==1]):ax.plot(x,curve,color=red,lw=.85,alpha=.8,label='Abnormal  individual waveforms' if i==0 else None)
 ax.set_title(f'{panel}   {f["display_date"]}   {f["wire_gauge_awg"]} AWG\nNormal: {int((y==0).sum()):,}; Abnormal: {int((y==1).sum()):,}',loc='left',fontsize=9,weight='bold')
 ax.set_xlim(1,200);ax.set_ylabel('Signal (native export scale)');ax.grid(alpha=.17)
 ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
 if letter in 'EF':ax.set_xlabel('Within-operation point index')
handles,labels=axs.flat[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.005),frameon=False,fontsize=8,ncol=1)
fig.tight_layout(rect=(0,.09,1,1),h_pad=1.0,w_pad=1.2)
fig.savefig(out/'figure3_waveforms.png');fig.savefig(out/'figure3_waveforms.svg');plt.close(fig)
(out/'figure_metadata.json').write_text(json.dumps({'display_date_note':'Visible dates are filename identifiers, not independently verified acquisition dates.','display_classes':{'0':'Normal','1':'Abnormal'},'files':files,'examples':example_info,'overview':'All label-1 curves; pointwise median and 5th–95th percentiles of all label-0 curves in each batch; no scaling, alignment, smoothing or resampling.'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Created Figure 3, and Figure 2 when original exports were supplied.')
