"""Produce editable slide chart data from the research outputs."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from analyze import ROOT,OUT,LABELS

COLORS=['#176D86','#B65A27','#6B7597','#46896A','#A45573','#9F8937','#568EAB','#7D6E61','#435A77','#815D9E','#926246','#386C65','#AA7F4B','#707C45','#6A7480']

def clean(obj):
    if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items()}
    if isinstance(obj,list):return [clean(v) for v in obj]
    if isinstance(obj,(np.integer,)):return int(obj)
    if isinstance(obj,(float,np.floating)):return None if not np.isfinite(obj) else float(obj)
    return obj

def main():
    n=pd.read_csv(OUT/'network_summary.csv');nets=n.network.tolist();cats=[x.upper() for x in nets]
    r=pd.read_csv(OUT/'reviewed_summary_long.csv');rv=pd.read_csv(OUT/'revision_summary_long.csv')
    mm=pd.read_csv(OUT/'reviewed_by_magnitude.csv');pm=pd.read_csv(OUT/'revision_by_magnitude.csv')
    audit=json.loads((OUT/'coverage_report.json').read_text());slides=[]
    def series(name,values,color=COLORS[0]):return dict(name=name,values=list(values),fill=color)
    def chart(title,values,format='0.0',max=None,categories=None):
        return dict(title=title,type='bar',categories=categories or cats,series=values,numberFormat=format,max=max)
    def median(table,metric,label,color=COLORS[0]):
        d=table[table.metric.eq(metric)].set_index('network').reindex(nets)
        return series(label,d['median'],color)
    def add(title,charts,caption,source,notes=''):
        slides.append(dict(title=title,charts=charts,caption=caption,source=source,notes=notes))
    add('33,468 earthquakes across 15 preferred networks',[
      chart('Events by preferred origin network',[series('Events',n.events)],'#,##0'),
      chart('Reported magnitude range',[series('Minimum',n.mag_min),series('Median',n.mag_median,COLORS[1]),series('Maximum',n.mag_max,COLORS[2])],'0.0')],
      '11 August–10 November 2026 UTC. Worldwide earthquakes, all magnitudes. Magnitude scales differ among providers.', 'network_summary.csv',
      'The primary grouping is the catalog preferred origin network, an operational proxy for authority. USGS preferences include geographic authority, source and update time. These volumes measure the ComCat cohort, not each network’s entire local catalog.')
    mag=pd.read_csv(OUT/'magnitude_counts.csv').pivot(index='network',columns='mag_bin',values='events').reindex(nets).fillna(0)
    spec=chart('Event composition by magnitude',[series(label,mag.get(label,pd.Series(0,index=nets)),COLORS[i]) for i,label in enumerate(LABELS)],'#,##0')
    spec['stacked']=True
    add('Magnitude coverage differs across network cohorts',[spec],
      'Bins are left-inclusive and right-exclusive. Preferred catalog magnitudes determine event-count strata. Counts overlap neither networks nor bins.', 'magnitude_counts.csv')
    add('Automatic submissions and review coverage',[
      chart('Events with observed automatic origins (%)',[series('Automatic history',100*n.observed_automatic_events/n.history_available,COLORS[1])],'0.0',100),
      chart('Reviewed origins and paired histories (%)',[series('Reviewed',100*n.reviewed_events/n.events),series('Automatic–reviewed pair',100*n.automatic_reviewed_pairs/n.events,COLORS[1])],'0.0',100)],
      'Observed publication comes from archived origin versions. Absence of retained automatic history does not prove that a network never publishes automatically.', 'network_summary.csv',
      f"Coverage: {audit['history_downloads']:,} histories from {audit['catalog_events']:,} cohort events. Paired events: {audit['automatic_reviewed_pairs']:,}. Archive acquisition uses the documented PDL west products_created_after stream and cached pilot FDSN detail responses.")
    add('Automatic-to-reviewed location and time revisions',[
      chart('Median epicentral separation (km)',[median(rv,'epicentral_shift_km','Median')],'0.00'),
      chart('Median absolute origin-time change (s)',[median(rv,'abs_delta_time_s','Median')],'0.00')],
      'Earliest retained automatic origin versus latest reviewed origin from the same network and product code. Revisions measure change, not independent accuracy.', 'revision_summary_long.csv')
    add('Magnitude and depth revisions',[
      chart('Median absolute magnitude change',[median(rv,'abs_delta_mag_same_type','Same-type magnitude')],'0.00'),
      chart('Median absolute depth change (km)',[median(rv,'abs_delta_depth_km','Depth')],'0.00')],
      'Magnitude differences require identical reported magnitude types. Depth and epicentral change remain separate measurements.', 'revision_summary_long.csv')
    add('Signed magnitude changes and scale transitions',[
      chart('Median signed magnitude change',[median(rv,'delta_mag_same_type','Reviewed minus automatic')],'0.00'),
      chart('Paired events with a magnitude-type change',[series('Different magnitude type',n.magnitude_type_changes,COLORS[1])],'#,##0')],
      'A change in magnitude type prevents a like-for-like magnitude comparison. Full paired values and type strings remain available.', 'automatic_to_reviewed.csv')
    for metrics,title in [(['horizontal_error_km','depth_error_km'],'Paired location uncertainty fields'),(['time_error_s','mag_error'],'Paired time and magnitude uncertainty fields')]:
        labels={'horizontal_error_km':'Horizontal uncertainty (km)','depth_error_km':'Depth uncertainty (km)','time_error_s':'Time uncertainty (s)','mag_error':'Magnitude uncertainty'}
        add(title,[chart(labels[k],[median(rv,'automatic_'+k,'Automatic',COLORS[1]),median(rv,'reviewed_'+k,'Reviewed')],'0.00') for k in metrics],
          'Stage-specific medians in paired events. Confidence levels and uncertainty definitions vary. Matched uncertainty deltas and field-specific n accompany the CSV summaries.', 'revision_summary_long.csv')
    add('Reviewed phase support and P/S balance',[
      chart('Median associated pick count',[median(r,'associated_pick_count','Associated picks')],'0'),
      chart('Median P/S ratio',[median(r,'P_S_ratio','P/S')],'0.00')],
      'Only picks referenced by the selected reviewed origin enter counts. Zero-S events have undefined P/S. These counts include associated picks regardless of location weight.', 'reviewed_summary_long.csv')
    add('P and S counts in reviewed origins',[
      chart('Median P and S counts',[median(r,'P_count','P'),median(r,'S_count','S',COLORS[1])],'0'),
      chart('Median provider-reported used-phase count',[median(r,'num_phases_used','Used phases')],'0')],
      'P/S families follow the first letter of the reported phase name. Provider used-phase counts may differ from associated observations and explicit time-weight counts.', 'reviewed_summary_long.csv')
    add('Reviewed network geometry',[
      chart('Median azimuthal gap (degrees)',[median(r,'gap_deg','Gap')],'0'),
      chart('Median minimum station distance (km)',[median(r,'minimum_distance_km','Minimum distance')],'0.0')],
      'Geometry comes from the selected reviewed origin. Minimum distance is epicentral distance converted from degrees with a mean Earth radius.', 'reviewed_summary_long.csv')
    for fam in ['P','S']:
        add(f'Local {fam} support within 10, 20 and 30 km',[
          chart(f'Median associated {fam} picks',[median(r,f'{fam}_within_{k}_km',f'≤{k} km',COLORS[i]) for i,k in enumerate([10,20,30])],'0.0'),
          chart(f'Median explicitly used {fam} picks',[median(r,f'{fam}_used_within_{k}_km',f'≤{k} km',COLORS[i]) for i,k in enumerate([10,20,30])],'0.0')],
          'Inclusive epicentral thresholds count picks, rather than unique stations. Explicit use requires positive time weight or timeUsed=true. Unknown distances remain unavailable.', 'reviewed_summary_long.csv')
    add('P polarity coverage in reviewed solutions',[
      chart('Median event-level P polarity fraction (%)',[median(r,'P_polarity_fraction','Event median')],'0.0',100),
      chart('All P picks with encoded polarity (%)',[series('Pick-weighted coverage',n.polarity_percent_P)],'0.0',100)],
      'Marked polarities are positive or negative. The denominator is all associated P picks. This measures encoded coverage, rather than polarity correctness.', 'reviewed_summary_long.csv and network_summary.csv')
    # Percent convert the event-level fraction, keeping original CSV units.
    slides[-1]['charts'][0]['series'][0]['values']=[v*100 if pd.notna(v) else np.nan for v in slides[-1]['charts'][0]['series'][0]['values']]
    add('Automatic picks can remain in reviewed origins',[
      chart('Automatic picks among known modes (%)',[series('Automatic / (automatic + manual)',n.automatic_percent_known,COLORS[1])],'0.0',100),
      chart('Associated picks with known evaluation mode (%)',[series('Known evaluation mode',n.known_mode_percent)],'0.0',100)],
      'Both charts are pick-weighted. Unknown evaluation mode cannot establish manual measurement. A reviewed origin can retain explicitly automatic picks.', 'network_summary.csv')
    add('Reviewed origins containing automatic picks',[
      chart('Reviewed phase events with ≥1 automatic pick (%)',[series('At least one automatic pick',100*n.reviewed_with_automatic_picks/n.matched_phase_events,COLORS[1])],'0.0',100),
      chart('Events with available reviewed phase data',[series('Reviewed phase events',n.matched_phase_events)],'#,##0')],
      'The percentage denominator is the network’s reviewed events with matching phase data. Explicit automatic flags describe exported records and may not capture every human edit.', 'network_summary.csv')
    for metrics,title in [(['horizontal_error_km','depth_error_km'],'Reported uncertainty in reviewed origins'),(['time_error_s','mag_error'],'Time and magnitude uncertainty in reviewed origins')]:
        labels={'horizontal_error_km':'Median horizontal uncertainty (km)','depth_error_km':'Median depth uncertainty (km)','time_error_s':'Median time uncertainty (s)','mag_error':'Median magnitude uncertainty'}
        add(title,[chart(labels[k],[median(r,k,'Reported uncertainty')],'0.00') for k in metrics],
          'Available reported values only. Missing fields remain missing. Zero-valued uncertainty does not establish perfect constraint. Cross-network calibration is unavailable.', 'reviewed_summary_long.csv')
    def trends(table,metric,title):
        vals=[]
        for i,net in enumerate(nets):
            d=table[table.network.eq(net)&table.metric.eq(metric)].set_index('mag_bin').reindex(LABELS)
            vals.append(series(net.upper(),d['median'].where(d.n.ge(20)),COLORS[i]))
        return dict(title=title,type='line',categories=LABELS,series=vals,numberFormat='0.0')
    add('Phase support and geometry across magnitude bins',[
       trends(mm,'associated_pick_count','Median associated picks'),trends(mm,'gap_deg','Median azimuthal gap (degrees)')],
       'Network medians require at least 20 events per metric and magnitude bin. Blank cells remain gaps. Reviewed magnitude determines the bin.', 'reviewed_by_magnitude.csv')
    add('Revision size across magnitude bins',[
       trends(pm,'epicentral_shift_km','Median epicentral revision (km)'),trends(pm,'abs_delta_mag_same_type','Median absolute magnitude revision')],
       'Paired medians require at least 20 events. Same-type magnitude comparisons only. Magnitude strata do not remove geography, depth or network-selection effects.', 'revision_by_magnitude.csv')
    add('Polarity and automatic picks across magnitude bins',[
       trends(mm,'P_polarity_fraction','Median P polarity fraction'),trends(mm,'automatic_fraction_known','Median automatic fraction among known modes')],
       'Values are event-level fractions from 0 to 1. Known-mode coverage must accompany automatic-pick fractions. Values require at least 20 events.', 'reviewed_by_magnitude.csv')
    cp=pd.read_csv(OUT/'cross_network_summary.csv');d=cp[cp.metric.eq('epicentral_shift_km')].sort_values('n',ascending=False).head(12)
    if len(d):
        cc=[f'{a.upper()} / {b.upper()} (n={int(z)})' for a,b,z in zip(d.network,d.reference_network,d.n)]
        add('Shared earthquakes allow a separate network comparison',[
          chart('Median separation of reviewed origins (km)',[series('Other network versus preferred network',d['median'])],'0.00',categories=cc)],
          'Most populated overlapping reviewed-network pairs. The preferred origin supplies the reference. Selected overlaps do not determine which solution is accurate.', 'cross_network_summary.csv')
    slides.append(dict(title='Interpretation and reproducibility',paragraphs=[
      'Catalog volume and magnitude range describe different earthquake populations and reporting thresholds.',
      'Automatic-to-reviewed changes quantify revisions. Independent ground truth would be needed to rank location accuracy.',
      'Pick metadata and uncertainty conventions constrain comparisons. Unknown values remain explicit.',
      'The GitHub repository contains event tables, paired product IDs, methods, publication figures and the frozen archive snapshot.'],
      caption='All network comparisons are descriptive. Full distributions and per-metric sample sizes accompany every summary.',source='METHODS.md',notes='Primary references: https://earthquake.usgs.gov/fdsnws/event/1/ ; https://earthquake.usgs.gov/data/catalog/products.php ; https://earthquake.usgs.gov/data/products/ ; https://quake.ethz.ch/quakeml/docs/REC?action=AttachFile&do=get&target=QuakeML-BED-20130214b.pdf'))
    spec=clean(dict(slides=slides,network_order=nets,coverage=audit,repository='https://github.com/dsiervo/usgs-catalog-network-comparison-2026'))
    (ROOT/'presentation'/'slide_data.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    print('Created data for',len(slides),'content slides')

if __name__=='__main__':main()
