"""Download a reproducible ComCat cohort and versioned product metadata.

No unit tests or checksum verification. Resume uses existing valid JSON/XML files.
"""
import argparse, concurrent.futures as cf, datetime as dt, gzip, json, math
import threading, time, urllib.request, urllib.parse, urllib.error, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / '.cache'
DATA = ROOT / 'data'
START = '2026-08-11T00:00:00'
END = '2026-11-11T00:00:00'
BASE = 'https://earthquake.usgs.gov/fdsnws/event/1/'
KM_DEG = math.pi * 6371.0088 / 180
RATE_LOCK=threading.Lock()
NEXT_REQUEST={}

def pace(url):
    # FDSN explicitly limits requests to 500 per five minutes. Bulk archive
    # requests are also paced, independently from static product downloads.
    key='fdsn' if '/fdsnws/' in url else 'bulk' if 'products_created_after' in url else 'static'
    interval={'fdsn':.8,'bulk':1.0,'static':.1}[key]
    with RATE_LOCK:
        now=time.monotonic(); wait=max(0,NEXT_REQUEST.get(key,0)-now)
        NEXT_REQUEST[key]=now+wait+interval
    if wait:time.sleep(wait)

def get(url, path):
    if path.exists():
        return gzip.decompress(path.read_bytes())
    for attempt in range(6):
        try:
            pace(url)
            req = urllib.request.Request(url, headers={'User-Agent': 'ComCatNetworkResearch/1.0 (public reproducible catalog study)'})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(body))
            return body
        except Exception as ex:
            if attempt == 5: raise
            if isinstance(ex,urllib.error.HTTPError) and ex.code==429:
                with RATE_LOCK:
                    NEXT_REQUEST['fdsn']=max(NEXT_REQUEST.get('fdsn',0),time.monotonic()+310)
                print('Rate limit: pausing event API for at least five minutes',flush=True)
                time.sleep(55)
            else:time.sleep(min(2 ** attempt, 20))

def jget(url, path): return json.loads(get(url, path))
def savej(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')
def number(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def stamp(v):
    try: return dt.datetime.fromisoformat(v.replace('Z', '+00:00')).timestamp()
    except (TypeError, ValueError, AttributeError): return None
def txt(e, p):
    v = e.find(p)
    return v.text.strip() if v is not None and v.text else None
def val(e, p): return number(txt(e, p))

FIELDS = {'mag':'magnitude','latitude':'latitude','longitude':'longitude','depth_km':'depth',
 'time_error_s':'eventtime-error','horizontal_error_km':'horizontal-error','depth_error_km':'vertical-error',
 'mag_error':'magnitude-error','gap_deg':'azimuthal-gap','minimum_distance_deg':'minimum-distance',
 'num_phases_used':'num-phases-used','num_stations_used':'num-stations-used','rms_s':'standard-error'}

def product_row(p):
    a = p['properties']
    r = {k:number(a.get(v)) for k,v in FIELDS.items()}
    r.update(product_id=p['id'], product_source=p['source'], network=a.get('origin-source',p['source']).lower(),
      code=p['code'], update_ms=p['updateTime'], review_status=a.get('review-status'),
      origin_time=a.get('eventtime'), mag_type=a.get('magnitude-type'),
      origin_id=a.get('quakeml-origin-publicid'), preferred_weight=p.get('preferredWeight'))
    r['minimum_distance_km'] = r['minimum_distance_deg'] * KM_DEG if r['minimum_distance_deg'] is not None else None
    return r

def phase_metrics(body, expected):
    root = ET.fromstring(body)
    for e in root.iter(): e.tag = e.tag.split('}')[-1]
    origins = root.findall('.//event/origin')
    origin = next((e for e in origins if e.get('publicID') == expected), None)
    if origin is None:
        return {'phase_status':'origin_id_mismatch', 'xml_origin_count':len(origins)}
    picks = {e.get('publicID'):e for e in root.findall('.//event/pick')}
    arrs = origin.findall('arrival')
    result = {'phase_status':'ok','arrival_count':len(arrs), 'xml_pick_count':len(picks),
              'origin_evaluation_mode':txt(origin,'evaluationMode'), 'origin_evaluation_status':txt(origin,'evaluationStatus')}
    for k,p in [('xml_used_phase_count','quality/usedPhaseCount'),('xml_associated_phase_count','quality/associatedPhaseCount'),
       ('xml_used_station_count','quality/usedStationCount'),('xml_gap_deg','quality/azimuthalGap'),
       ('xml_minimum_distance_deg','quality/minimumDistance'),('xml_time_uncertainty_s','time/uncertainty'),
       ('xml_depth_uncertainty_m','depth/uncertainty'),('xml_latitude_uncertainty_deg','latitude/uncertainty'),
       ('xml_longitude_uncertainty_deg','longitude/uncertainty'),
       ('xml_horizontal_uncertainty_m','originUncertainty/horizontalUncertainty'),
       ('xml_min_horizontal_uncertainty_m','originUncertainty/minHorizontalUncertainty'),
       ('xml_max_horizontal_uncertainty_m','originUncertainty/maxHorizontalUncertainty'),
       ('xml_uncertainty_confidence_level','originUncertainty/confidenceLevel')]: result[k] = val(origin,p)
    result['xml_preferred_uncertainty_description'] = txt(origin,'originUncertainty/preferredDescription')
    records, seen = [],set()
    for a in arrs:
        pid = txt(a,'pickID')
        if pid in seen: continue
        seen.add(pid)
        pick = picks.get(pid)
        phase = txt(a,'phase') or (txt(pick,'phaseHint') if pick is not None else '') or ''
        family = 'P' if phase.upper().startswith('P') else 'S' if phase.upper().startswith('S') else 'other'
        distance = val(a,'distance')
        w = val(a,'timeWeight')
        used = (w > 0) if w is not None else (txt(a,'timeUsed') == 'true' if txt(a,'timeUsed') is not None else None)
        records.append({'family':family,'distance_km':distance * KM_DEG if distance is not None else None,
          'mode':txt(pick,'evaluationMode') if pick is not None else None,
          'polarity':txt(pick,'polarity') if pick is not None else None,
          'resolved':pick is not None,'used':used})
    result.update(associated_pick_count=len(records), unresolved_pick_count=sum(not r['resolved'] for r in records),
       automatic_pick_count=sum(r['mode']=='automatic' for r in records),
       manual_pick_count=sum(r['mode']=='manual' for r in records),
       unknown_mode_pick_count=sum(r['mode'] not in ('automatic','manual') for r in records),
       used_pick_count=sum(r['used'] is True for r in records),
       unknown_weight_pick_count=sum(r['used'] is None for r in records))
    for fam in ['P','S']:
        rs = [r for r in records if r['family']==fam]
        result[f'{fam}_count']=len(rs)
        result[f'{fam}_used_count']=sum(r['used'] is True for r in rs)
        result[f'{fam}_distance_known_count']=sum(r['distance_km'] is not None for r in rs)
        for radius in [10,20,30]:
            result[f'{fam}_within_{radius}_km']=sum(r['distance_km'] is not None and r['distance_km']<=radius for r in rs)
            result[f'{fam}_used_within_{radius}_km']=sum(r['used'] is True and r['distance_km'] is not None and r['distance_km']<=radius for r in rs)
        if fam=='P': result['P_marked_polarity_count']=sum(r['polarity'] in ('positive','negative') for r in rs)
    return result

def catalog():
    start, end = dt.datetime.fromisoformat(START),dt.datetime.fromisoformat(END)
    windows=[]
    while start < end:
        stop=min(start+dt.timedelta(days=7),end)
        windows.append((start,stop)); start=stop
    def fetch(w):
        a,b=w
        args={'format':'geojson','starttime':a.isoformat(),'endtime':b.isoformat(), 'eventtype':'earthquake','limit':20000,'orderby':'time-asc'}
        return jget(BASE+'query?'+urllib.parse.urlencode(args),CACHE/'catalog'/f'{a.date()}.json.gz')
    results=list(cf.ThreadPoolExecutor(max_workers=4).map(fetch,windows))
    features={f['id']:f for d in results for f in d['features'] if stamp(START+'Z')*1000<=f['properties']['time']<stamp(END+'Z')*1000}
    ordered=sorted(features.values(),key=lambda f:(f['properties']['time'],f['id']))
    rows=[]
    for f in ordered:
        p=f['properties']; lon,lat,dep=f['geometry']['coordinates']
        rows.append(dict(event_id=f['id'],network=p['net'],origin_time=dt.datetime.fromtimestamp(p['time']/1000,dt.timezone.utc).isoformat(),
          mag=p['mag'],mag_type=p['magType'],latitude=lat,longitude=lon,depth_km=dep,review_status=p['status'],
          gap_deg=p['gap'],minimum_distance_deg=p['dmin'],num_stations=p['nst'],rms_s=p['rms'],sources=p['sources'],
          url=p['url'],detail_url=p['detail'],updated_ms=p['updated']))
    import pandas as pd
    DATA.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(DATA/'catalog.csv',index=False)
    savej(DATA/'cohort.json',{'start_inclusive_utc':START+'Z','end_exclusive_utc':END+'Z','event_type':'earthquake',
        'geography':'worldwide','minimum_magnitude':None,'n_events':len(rows),'catalog_retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'queries':[d['metadata'] for d in results]})
    print('Catalog:',len(rows),'events',flush=True)
    return rows

def process_event(e, phases=True):
    eid,net=e['event_id'],e['network']
    out=CACHE/'extracted'/f'{eid}.json.gz'
    if out.exists(): return json.loads(gzip.decompress(out.read_bytes()))
    url=BASE+'query?'+urllib.parse.urlencode({'eventid':eid,'format':'geojson','includesuperseded':'true'})
    normalized=CACHE/'normalized'/f'{eid}.json.gz'
    d=json.loads(gzip.decompress(normalized.read_bytes())) if normalized.exists() else jget(url,CACHE/'details'/f'{eid}.json.gz')
    products=d['properties'].get('products',{})
    origins=[p for p in products.get('origin',[]) if p.get('status')=='UPDATE']
    rows=[product_row(p) for p in origins]
    contrib=[]
    for source in sorted(set(r['network'] for r in rows)):
        rs=[r for r in rows if r['network']==source]
        last=max(rs,key=lambda r:r['update_ms'])
        contrib.append(dict(event_id=eid,network=source,preferred_network=net,origin_versions=len(rs),
           ever_automatic=any(r['review_status']=='automatic' for r in rs),ever_reviewed=any(r['review_status']=='reviewed' for r in rs),
           latest_review_status=last['review_status'],mag=last['mag'],mag_type=last['mag_type']))
    own=[r for r in rows if r['network']==net]
    reviewed=[r for r in own if r['review_status']=='reviewed']
    final=max(reviewed,key=lambda r:r['update_ms']) if reviewed else None
    automatic=[r for r in own if r['review_status']=='automatic']
    result={'event_id':eid,'network':net,'history_status':'ok','origin_versions':len(own),
       'ever_automatic':bool(automatic),'ever_reviewed':bool(reviewed),'contributions':contrib,'reviewed':final,'automatic':None,
       'phase':{'phase_status':'no_reviewed_origin'}, 'history_url':url}
    result['history_transport']=d.get('research_provenance',{}).get('transport','FDSN event detail')
    if final:
        eligible=[r for r in automatic if r['update_ms']<final['update_ms'] and r['code']==final['code']]
        result['automatic']=min(eligible,key=lambda r:r['update_ms']) if eligible else None
        candidates=[p for p in products.get('phase-data',[]) if p.get('status')=='UPDATE' and
            p['properties'].get('origin-source',p['source']).lower()==net and
            p['properties'].get('quakeml-origin-publicid')==final['origin_id'] and p['properties'].get('review-status')=='reviewed']
        result['phase']={'phase_status':'no_matching_reviewed_phase_product'}
        if candidates and phases:
            p=max(candidates,key=lambda p:p['updateTime'])
            contents=p.get('contents',{})
            content=contents.get('quakeml.xml') or next((v for k,v in contents.items() if k.endswith('.xml') and 'quakeml' in k.lower()),None)
            if content:
                try:
                    body=get(content['url'],CACHE/'phases'/f'{eid}.xml.gz')
                    result['phase']=phase_metrics(body,final['origin_id'])
                    result['phase'].update(phase_product_id=p['id'],phase_url=content['url'])
                except Exception as ex: result['phase']={'phase_status':'download_or_parse_error','phase_error':str(ex)}
            else: result['phase']={'phase_status':'no_quakeml_content'}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(gzip.compress(json.dumps(result).encode()))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=12);ap.add_argument('--limit',type=int);ap.add_argument('--catalog-only',action='store_true');args=ap.parse_args()
    events=catalog()
    if args.catalog_only:return
    if args.limit:events=events[:args.limit]
    done=0;errors=[];t=time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(process_event,e):e for e in events}
        for f in cf.as_completed(jobs):
            e=jobs[f]
            try:f.result()
            except Exception as ex:errors.append({'event_id':e['event_id'],'error':str(ex)})
            done+=1
            if done%100==0 or done==len(events):print(f'{done}/{len(events)} events, {len(errors)} failures, {done/max(1,time.time()-t):.1f} events/s',flush=True)
    savej(DATA/'acquisition_errors.json',errors)
    print('Acquisition complete',flush=True)

if __name__=='__main__':main()
