"""Derive event tables, descriptive summaries and publication figure inputs."""
import gzip,json,math,platform,sys,concurrent.futures as cf
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Geod
from acquire import ROOT,CACHE,DATA,product_row,stamp

OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
GEOD=Geod(ellps='WGS84')
BINS=[-np.inf,0,1,2,3,4,5,np.inf]
LABELS=['M<0','0–1','1–2','2–3','3–4','4–5','M≥5']
NAMES={'ak':'Alaska Earthquake Center','av':'Alaska Volcano Observatory','ci':'Southern California Seismic Network',
 'hv':'Hawaiian Volcano Observatory','mb':'Montana Bureau of Mines and Geology','nc':'Northern California Seismic System',
 'nm':'New Madrid Seismic Network','nn':'Nevada Seismological Laboratory','ok':'Oklahoma Geological Survey',
 'pr':'Puerto Rico Seismic Network','se':'CERI Southeastern US','tx':'TexNet','us':'USGS NEIC',
 'uu':'University of Utah Seismograph Stations','uw':'Pacific Northwest Seismic Network'}

def write(df,name):df.to_csv(OUT/name,index=False)
def magbin(s):return pd.cut(s,BINS,labels=LABELS,right=False).astype('str')
def delta(a,b):
    r={}
    for key in ['mag','depth_km','time_error_s','horizontal_error_km','depth_error_km','mag_error']:
        r['automatic_'+key]=a.get(key);r['reviewed_'+key]=b.get(key)
        r['delta_'+key]=(b[key]-a[key]) if a.get(key) is not None and b.get(key) is not None else None
    r['automatic_mag_type']=a['mag_type'];r['reviewed_mag_type']=b['mag_type']
    r['same_mag_type']=a['mag_type']==b['mag_type'] and bool(a['mag_type'])
    r['automatic_product_id']=a['product_id'];r['reviewed_product_id']=b['product_id']
    r['automatic_update_ms']=a['update_ms'];r['reviewed_update_ms']=b['update_ms']
    at,bt=stamp(a.get('origin_time')),stamp(b.get('origin_time'))
    r['delta_time_s']=bt-at if at is not None and bt is not None else None
    try:r['epicentral_shift_km']=GEOD.inv(a['longitude'],a['latitude'],b['longitude'],b['latitude'])[2]/1000
    except (TypeError,ValueError):r['epicentral_shift_km']=None
    for k in ['delta_mag','delta_depth_km','delta_time_s']:
        r['abs_'+k]=abs(r[k]) if r[k] is not None else None
    r['delta_mag_same_type']=r['delta_mag'] if r['same_mag_type'] else None
    r['abs_delta_mag_same_type']=r['abs_delta_mag'] if r['same_mag_type'] else None
    return r

def summary_long(frame,groups,metrics):
    rows=[]
    for keys,d in frame.groupby(groups,observed=True,dropna=False):
        if not isinstance(keys,tuple):keys=(keys,)
        for metric in metrics:
            s=pd.to_numeric(d[metric],errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
            qs=s.quantile([.1,.25,.5,.75,.9,.95]) if len(s) else pd.Series(dtype=float)
            rows.append(dict(zip(groups,keys))|dict(metric=metric,n_total=len(d),n=len(s),missing=len(d)-len(s),
                mean=s.mean(),q10=qs.get(.1),q25=qs.get(.25),median=qs.get(.5),q75=qs.get(.75),q90=qs.get(.9),q95=qs.get(.95)))
    return pd.DataFrame(rows)

def main():
    cat=pd.read_csv(DATA/'catalog.csv'); available=[];contributions=[];manual=[];pairs=[];lastpairs=[];versions=[];cross=[]
    def load_event(e):
        path=CACHE/'extracted'/f"{e['event_id']}.json.gz"
        if not path.exists():return e,None,None
        rawpath=CACHE/'normalized'/f"{e['event_id']}.json.gz"
        if not rawpath.exists():rawpath=CACHE/'details'/f"{e['event_id']}.json.gz"
        return e,json.loads(gzip.decompress(path.read_bytes())),json.loads(gzip.decompress(rawpath.read_bytes()))
    pool=cf.ThreadPoolExecutor(max_workers=24)
    for i,(e,d,raw) in enumerate(pool.map(load_event,cat.to_dict('records'),buffersize=96)):
        if d is None:continue
        b=d['reviewed'];a=d['automatic']
        available.append({k:d.get(k) for k in ['event_id','network','history_status','origin_versions','ever_automatic','ever_reviewed']}|d['phase'])
        contributions.extend(d['contributions'])
        if b:
            row={**b,**d['phase'],'event_id':e['event_id'],'network':e['network'],'catalog_mag':e['mag']}
            manual.append(row)
        if a and b:pairs.append({'event_id':e['event_id'],'network':e['network'],'mag':b['mag'],**delta(a,b)})
        rs=[product_row(p)|{'event_id':e['event_id'],'preferred_network':e['network']} for p in raw['properties'].get('products',{}).get('origin',[]) if p.get('status')=='UPDATE']
        versions.extend(rs)
        if b:
            autos=[r for r in rs if r['network']==e['network'] and r['code']==b['code'] and r['review_status']=='automatic' and r['update_ms']<b['update_ms']]
            if autos:lastpairs.append({'event_id':e['event_id'],'network':e['network'],'mag':b['mag'],**delta(max(autos,key=lambda r:r['update_ms']),b)})
            for net in set(r['network'] for r in rs)-{e['network']}:
                candidates=[r for r in rs if r['network']==net and r['review_status']=='reviewed']
                if candidates:
                    other=max(candidates,key=lambda r:r['update_ms'])
                    cross.append({'event_id':e['event_id'],'network':net,'reference_network':e['network'],'mag':b['mag'],**delta(other,b)})
        if i%5000==0:print('Derived',i,'events',flush=True)
    hist=pd.DataFrame(available);hist.to_csv(OUT/'event_history_and_phase_coverage.csv.gz',index=False)
    c=cat.merge(hist[['event_id','history_status','origin_versions','ever_automatic','ever_reviewed','phase_status']],on='event_id',how='left')
    c['mag_bin']=magbin(c['mag']);c['week']=pd.to_datetime(c.origin_time,utc=True,format='ISO8601').dt.to_period('W-SUN').astype(str).str[:10]
    write(c,'cohort_with_coverage.csv')
    contrib=pd.DataFrame(contributions);write(contrib,'network_contributions.csv')
    v=pd.DataFrame(versions);v.to_csv(OUT/'origin_versions.csv.gz',index=False)
    m=pd.DataFrame(manual)
    for col in ['associated_pick_count','P_count','S_count','automatic_pick_count','manual_pick_count','unknown_mode_pick_count','P_marked_polarity_count']:
        if col not in m:m[col]=np.nan
    m['mag_bin']=magbin(m['mag'])
    m['P_S_ratio']=m.P_count/m.S_count.replace(0,np.nan)
    m['P_polarity_fraction']=m.P_marked_polarity_count/m.P_count.replace(0,np.nan)
    m['automatic_fraction_all']=m.automatic_pick_count/m.associated_pick_count.replace(0,np.nan)
    m['known_mode_fraction']=(m.automatic_pick_count+m.manual_pick_count)/m.associated_pick_count.replace(0,np.nan)
    m['automatic_fraction_known']=m.automatic_pick_count/(m.automatic_pick_count+m.manual_pick_count).replace(0,np.nan)
    m['any_automatic_pick']=np.where(m.phase_status.eq('ok') & m.associated_pick_count.gt(0),m.automatic_pick_count.gt(0).astype(float),np.nan)
    m['mag_bin']=magbin(m.mag)
    m.to_csv(OUT/'reviewed_event_metrics.csv.gz',index=False)
    p=pd.DataFrame(pairs);lp=pd.DataFrame(lastpairs);cp=pd.DataFrame(cross)
    for frame,name in [(p,'automatic_to_reviewed.csv'),(lp,'last_automatic_to_reviewed.csv'),(cp,'other_network_to_preferred_reviewed.csv')]:
        if len(frame):frame['mag_bin']=magbin(frame.mag)
        write(frame,name)
    counts=[]
    for net,d in c.groupby('network'):
        md=m[m.network.eq(net)];ph=md[md.phase_status.eq('ok')];pr=p[p.network.eq(net)]
        modes=ph[['automatic_pick_count','manual_pick_count','unknown_mode_pick_count']].sum()
        allp=modes.sum();known=modes['automatic_pick_count']+modes['manual_pick_count']
        counts.append(dict(network=net,name=NAMES.get(net,net),events=len(d),mag_min=d.mag.min(),mag_q10=d.mag.quantile(.1),mag_median=d.mag.median(),mag_q90=d.mag.quantile(.9),mag_max=d.mag.max(),
            latest_catalog_automatic=int(d.review_status.eq('automatic').sum()),history_available=d.history_status.eq('ok').sum(),
            observed_automatic_events=d.ever_automatic.fillna(False).sum(),reviewed_events=len(md),matched_phase_events=len(ph),automatic_reviewed_pairs=len(pr),
            magnitude_type_changes=(~pr.same_mag_type).sum(),
            associated_picks=ph.associated_pick_count.sum(),P_picks=ph.P_count.sum(),S_picks=ph.S_count.sum(),
            P_polarities=ph.P_marked_polarity_count.sum(),automatic_picks=modes['automatic_pick_count'],manual_picks=modes['manual_pick_count'],unknown_mode_picks=modes['unknown_mode_pick_count'],
            known_mode_percent=100*known/allp if allp else np.nan,
            automatic_percent_known=100*modes['automatic_pick_count']/known if known else np.nan,
            polarity_percent_P=100*ph.P_marked_polarity_count.sum()/ph.P_count.sum() if ph.P_count.sum() else np.nan,
            reviewed_with_automatic_picks=int(ph.automatic_pick_count.gt(0).sum()),reviewed_zero_S=int(ph.S_count.eq(0).sum())))
    n=pd.DataFrame(counts).sort_values('events',ascending=False);write(n,'network_summary.csv')
    cs=contrib.groupby('network').agg(events_contributed=('event_id','nunique'),observed_automatic_events=('ever_automatic','sum'),reviewed_events=('ever_reviewed','sum'),
      mag_min=('mag','min'),mag_median=('mag','median'),mag_max=('mag','max')).reset_index();write(cs,'all_contributor_summary.csv')
    magcounts=c.groupby(['network','mag_bin'],observed=True).size().rename('events').reset_index();write(magcounts,'magnitude_counts.csv')
    ms=['associated_pick_count','used_pick_count','num_phases_used','P_count','S_count','P_S_ratio','gap_deg','minimum_distance_km','horizontal_error_km','depth_error_km','time_error_s','mag_error',
      'P_polarity_fraction','automatic_fraction_all','automatic_fraction_known','known_mode_fraction','any_automatic_pick']
    ms += [f'{f}_{s}within_{r}_km' for f in ['P','S'] for s in ['', 'used_'] for r in [10,20,30]]
    for col in ms:
        if col not in m:m[col]=np.nan
    write(summary_long(m,['network'],ms),'reviewed_summary_long.csv')
    write(summary_long(m,['network','mag_bin'],ms),'reviewed_by_magnitude.csv')
    metrics=['epicentral_shift_km','abs_delta_depth_km','abs_delta_time_s','delta_time_s','delta_mag_same_type','abs_delta_mag_same_type',
      'automatic_horizontal_error_km','reviewed_horizontal_error_km','delta_horizontal_error_km','automatic_depth_error_km','reviewed_depth_error_km','delta_depth_error_km',
      'automatic_time_error_s','reviewed_time_error_s','delta_time_error_s','automatic_mag_error','reviewed_mag_error','delta_mag_error']
    write(summary_long(p,['network'],metrics),'revision_summary_long.csv')
    write(summary_long(p,['network','mag_bin'],metrics),'revision_by_magnitude.csv')
    write(summary_long(lp,['network'],metrics),'last_automatic_revision_summary.csv')
    if len(cp):write(summary_long(cp,['network','reference_network'],['epicentral_shift_km','abs_delta_depth_km','abs_delta_time_s','abs_delta_mag_same_type']),'cross_network_summary.csv')
    weekly=c.groupby(['network','week']).agg(events=('event_id','size'),observed_automatic=('ever_automatic','sum'),history_available=('history_status',lambda s:s.eq('ok').sum())).reset_index()
    weekly['observed_automatic_percent']=100*weekly.observed_automatic/weekly.history_available;write(weekly,'weekly_automatic_coverage.csv')
    audit={'catalog_events':len(cat),'unique_event_ids':cat.event_id.nunique(),'history_downloads':len(hist),'missing_history':len(cat)-len(hist),'reviewed_events':len(m),
      'phase_status_counts':hist.phase_status.value_counts().to_dict(),'origin_versions':len(v),'contributing_networks':contrib.network.nunique(),
      'automatic_reviewed_pairs':len(p),'same_type_magnitude_pairs':int(p.same_mag_type.sum()),'cross_network_reviewed_comparisons':len(cp),
      'unresolved_pick_references':int(m.get('unresolved_pick_count',pd.Series(dtype=float)).sum()),
      'reported_zero_S_events':int(m.S_count.eq(0).sum()),'phase_distance_unknown_P':int((m.P_count-m.get('P_distance_known_count',0)).sum()),
      'phase_distance_unknown_S':int((m.S_count-m.get('S_distance_known_count',0)).sum()),
      'runtime':{'python':sys.version,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__}}
    (OUT/'coverage_report.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2),flush=True)

if __name__=='__main__':main()

