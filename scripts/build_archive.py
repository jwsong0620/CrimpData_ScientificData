"""Create a checksummed public ZIP from an allowlist; never include local source exports."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TOP=['README.md','LICENSE','CITATION.cff','requirements.txt','.gitignore','.gitattributes']
PATTERNS=['data/*.csv','metadata/*.csv','metadata/*.json','scripts/*.py',
          'docs/*.md','docs/*.txt','licenses/*.txt','validation/reference/*.json',
          'validation/reference/*.csv','validation/reference/*.txt','figures/reference/*.png']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-only',action='store_true')
    args=parser.parse_args()
    files={ROOT/name for name in TOP}
    for pattern in PATTERNS:files.update(ROOT.glob(pattern))
    manifest=ROOT/'metadata/package_manifest.json'
    files.discard(manifest)
    for p in files:
        if not p.is_file() or p.is_symlink() or ROOT not in p.resolve().parents:
            raise ValueError(f'Unexpected file: {p}')
    ordered=sorted(files,key=lambda p:p.relative_to(ROOT).as_posix())
    entries=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in ordered]
    version=json.loads((ROOT/'metadata/release.json').read_text(encoding='utf-8'))['version']
    manifest.write_text(json.dumps({'version':version,'scope':'Public package only; original exports and local reviewer evidence excluded.',
                                   'files':entries},indent=2)+'\n',encoding='utf-8')
    if args.manifest_only:
        print(f'Manifest refreshed for {len(entries)} public files.');return
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    target=out/f'crimp-production-data-v{version}.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in ordered+[manifest]:z.write(p,p.relative_to(ROOT).as_posix())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (out/(target.name+'.sha256')).write_text(digest+'  '+target.name+'\n',encoding='utf-8')
    print(f'Created {target.name}: {len(entries)+1} public files; {target.stat().st_size:,} bytes.')
    print('No original exports, local reviewer evidence, Git history, environments or manuscript files included.')


if __name__=='__main__':main()
