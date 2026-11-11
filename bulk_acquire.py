"""Read the documented ComCat archive stream in batches, then extract cohort.

This uses the archive's full notification products, not the 30-day realtime hub.
USGS documentation: ProductsCreatedAfterClient, /pdl/west/products_created_after.
"""
import concurrent.futures as cf,datetime as dt,gzip,json,sqlite3,time,urllib.parse
import pandas as pd
from acquire import ROOT,CACHE,DATA,START,END,get,savej,stamp,process_event

URL='https://earthquake.usgs.gov/pdl/west/products_created_after'

def normalize(p):
    i=p['id'];ms=round(stamp(i['updateTime'])*1000)
    contents=p.get('contents',{})
    if isinstance(contents,list):contents={v['path']:v for v in contents}
    return dict(id=f"urn:usgs-product:{i['source']}:{i['type']}:{i['code']}:{ms}",type=i['type'],source=i['source'],code=i['code'],
        updateTime=ms,status=p.get('status','UPDATE'),properties=p.get('properties',{}),contents=contents)

def main():
    DATA.mkdir(exist_ok=True);(CACHE/'bulk').mkdir(parents=True,exist_ok=True)
    cutoff_path=DATA/'bulk_snapshot.json'
    meta=json.loads(cutoff_path.read_text()) if cutoff_path.exists() else {'start_created_after_utc':'2026-08-10T00:00:00Z',
       'end_created_before_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'endpoint':URL,'batch_limit':1000}
    savej(cutoff_path,meta)
    cursor=meta['start_created_after_utc'];end=stamp(meta['end_created_before_utc']);page=0;total=0;t=time.time()
    db=sqlite3.connect(CACHE/'products.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, alias TEXT, type TEXT, payload TEXT)')
    db.execute('CREATE INDEX IF NOT EXISTS product_alias ON products(alias)')
    while stamp(cursor)<end:
        query=URL+'?'+urllib.parse.urlencode({'created_after':cursor,'limit':1000})
        path=CACHE/'bulk'/f'page-{page:05d}.json.gz'
        d=json.loads(get(query,path));ns=d.get('notifications',[])
        if not ns:break
        for n in ns:
            if stamp(n['created'])>end:continue
            p=normalize(n['product'])
            if p['type'] not in ('origin','phase-data'):continue
            a=p['properties'];alias=(a.get('eventsource','')+a.get('eventsourcecode','')).lower()
            if not alias:continue
            db.execute('INSERT OR REPLACE INTO products VALUES (?,?,?,?)',(p['id'],alias,p['type'],json.dumps(p)))
        db.commit();total+=len(ns)
        nxt=ns[-1]['created']
        if stamp(nxt)<=stamp(cursor):break
        cursor=nxt;page+=1
        if page%10==0:print(f'Archive page {page}: {cursor}, {total} notifications, elapsed {(time.time()-t)/60:.1f} min',flush=True)
        if len(ns)<1000:break
    print('Archive stream complete:',page,'pages',flush=True)
    aliasmap={}
    for f in (CACHE/'catalog').glob('*.gz'):
        d=json.loads(gzip.decompress(f.read_bytes()))
        for e in d['features']:
            aliases=[s for s in e['properties']['ids'].split(',') if s]
            aliasmap[e['id']]=aliases
    events=pd.read_csv(DATA/'catalog.csv').to_dict('records');missing=[]
    for e in events:
        eid=e['event_id'];ps={}
        orig=CACHE/'details'/f'{eid}.json.gz'
        if orig.exists():
            old=json.loads(gzip.decompress(orig.read_bytes()))
            for typ in ['origin','phase-data']:
                for p in old['properties'].get('products',{}).get(typ,[]):ps[p['id']]=p
        for alias in aliasmap.get(eid,[eid]):
            for (payload,) in db.execute('SELECT payload FROM products WHERE alias=?',(alias.lower(),)):
                p=json.loads(payload)
                if p['id'] not in ps:ps[p['id']]=p
        products={typ:[p for p in ps.values() if p['type']==typ] for typ in ['origin','phase-data']}
        if not products['origin']:missing.append(eid);continue
        normalized={'id':eid,'properties':{'products':products},'research_provenance':{'transport':'PDL archive stream plus cached FDSN detail','snapshot':meta}}
        out=CACHE/'normalized'/f'{eid}.json.gz';out.parent.mkdir(exist_ok=True)
        out.write_bytes(gzip.compress(json.dumps(normalized).encode()))
        # Re-extract prior pilot records with the more complete archive history.
        extracted=CACHE/'extracted'/f'{eid}.json.gz'
        if extracted.exists():extracted.unlink()
    db.close()
    savej(DATA/'bulk_coverage.json',{'notification_pages':page,'notifications_seen_including_boundary_repeats':total,
      'cohort_events':len(events),'events_without_bulk_or_cached_origins':missing,'end_cursor':cursor})
    print('Normalized events',len(events)-len(missing),'missing',len(missing),flush=True)
    errors=[];done=0;t=time.time()
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        jobs={pool.submit(process_event,e):e for e in events}
        for f in cf.as_completed(jobs):
            e=jobs[f]
            try:f.result()
            except Exception as ex:errors.append({'event_id':e['event_id'],'error':str(ex)})
            done+=1
            if done%500==0:print(f'Phase extraction {done}/{len(events)}, {len(errors)} errors, {done/max(time.time()-t,1):.1f} events/s',flush=True)
    savej(DATA/'acquisition_errors.json',errors)
    print('Bulk acquisition and phase extraction complete',flush=True)

if __name__=='__main__':main()
