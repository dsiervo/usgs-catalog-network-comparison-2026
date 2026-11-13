"""Package frozen source downloads as GitHub release assets, without checksums."""
import json,tarfile,io,concurrent.futures as cf
from pathlib import Path
from acquire import ROOT,CACHE
out=ROOT/'build'/'snapshot';out.mkdir(parents=True,exist_ok=True)
groups={}
for folder in ['bulk','catalog','details','normalized','phases','extracted']:
    for p in (CACHE/folder).glob('*.gz'):
        key='bulk' if folder=='bulk' else 'catalog' if folder=='catalog' else p.name[:2]
        groups.setdefault(key,[]).append(p)
manifest=[]
for group,files in sorted(groups.items()):
    target=out/f'snapshot-{group}.tar'
    with tarfile.open(target,'w') as t, cf.ThreadPoolExecutor(max_workers=24) as pool:
        for p,body in pool.map(lambda p:(p,p.read_bytes()),sorted(files),buffersize=96):
            info=tarfile.TarInfo(str(p.relative_to(ROOT)).replace('\\','/'));info.size=len(body)
            t.addfile(info,io.BytesIO(body))
    manifest.append({'asset':target.name,'files':len(files),'bytes':target.stat().st_size})
    print(group,len(files),target.stat().st_size,flush=True)
(ROOT/'data'/'snapshot_assets.json').write_text(json.dumps(manifest,indent=2))
