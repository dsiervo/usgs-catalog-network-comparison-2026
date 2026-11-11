"""Publication figures in PDF, SVG and 300-dpi PNG, with source tables."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from analyze import ROOT,OUT,LABELS,NAMES

FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
 'axes.titleweight':'bold','axes.labelsize':10,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
 'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'savefig.facecolor':'white'})
CAPTIONS={}

def finish(fig,stem,title,caption):
    fig.suptitle(title,x=.02,ha='left',fontsize=16,fontweight='bold')
    fig.subplots_adjust(top=.88,bottom=.13,left=.09,right=.96,wspace=.34,hspace=.5)
    for ext in ['pdf','svg','png']:fig.savefig(FIG/f'{stem}.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig);CAPTIONS[stem]={'title':title,'caption':caption}

def intervals(ax,table,metric,nets,label,color='#176D86',zero=False,log=False):
    d=table[table.metric.eq(metric)].set_index('network').reindex(nets)
    for i,(_,r) in enumerate(d.iterrows()):
        if pd.notna(r.get('median')) and r.get('n',0)>0:
            ax.plot([r.q10,r.q90],[i,i],color=color,lw=2,alpha=.6)
            ax.plot(r['median'],i,'o',color=color,ms=4)
            ax.text(1.01,i,f"{int(r['n']):,}",transform=ax.get_yaxis_transform(),va='center',fontsize=8,color='#555555')
    ax.set_yticks(range(len(nets)),[n.upper() for n in nets]);ax.invert_yaxis();ax.set_xlabel(label)
    ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    ax.text(1.01,1.02,'n',transform=ax.transAxes,color='#555555',fontsize=8)
    if zero:ax.axvline(0,color='#999999',lw=.7)
    if log:ax.set_xscale('symlog',linthresh=.1)

def heat(ax,df,nets,cols,title,fmt='.1f',cmap='viridis',vmin=None,vmax=None):
    arr=df.reindex(index=nets,columns=cols).to_numpy(dtype=float)
    im=ax.imshow(np.ma.masked_invalid(arr),aspect='auto',cmap=cmap,vmin=vmin,vmax=vmax)
    ax.set_xticks(range(len(cols)),cols,rotation=25,ha='right');ax.set_yticks(range(len(nets)),[n.upper() for n in nets]);ax.set_title(title,loc='left',fontsize=11,pad=10)
    mid=(np.nanmin(arr)+np.nanmax(arr))/2 if np.isfinite(arr).any() else 0
    for i,j in np.ndindex(arr.shape):
        s=format(arr[i,j],fmt) if np.isfinite(arr[i,j]) else '—'
        ax.text(j,i,s,ha='center',va='center',fontsize=8,color='white' if np.isfinite(arr[i,j]) and arr[i,j]<mid else '#202020')
    return im

def main():
    c=pd.read_csv(OUT/'cohort_with_coverage.csv');n=pd.read_csv(OUT/'network_summary.csv');nets=n.network.tolist()
    m=pd.read_csv(OUT/'reviewed_event_metrics.csv.gz');r=pd.read_csv(OUT/'reviewed_summary_long.csv');p=pd.read_csv(OUT/'automatic_to_reviewed.csv');rs=pd.read_csv(OUT/'revision_summary_long.csv')
    colors={net:plt.get_cmap('tab20')(i) for i,net in enumerate(nets)}
    fig,axs=plt.subplots(1,3,figsize=(14,6.5),gridspec_kw={'width_ratios':[1,1,1.2]})
    y=np.arange(len(nets));axs[0].barh(y,n.events,color='#176D86');axs[0].set_yticks(y,n.network.str.upper());axs[0].invert_yaxis();axs[0].set_xlabel('Preferred events')
    for i,v in enumerate(n.events):axs[0].text(v+max(n.events)*.015,i,f'{v:,}',va='center',fontsize=8)
    axs[0].set_xlim(0,max(n.events)*1.2)
    frac=100*n.observed_automatic_events/n.history_available
    axs[1].barh(y,frac,color='#B65A27');axs[1].set_yticks(y,n.network.str.upper());axs[1].invert_yaxis();axs[1].set_xlabel('Observed automatic history (%)');axs[1].set_xlim(0,110)
    for i,v in enumerate(frac):axs[1].text(v+1,i,f'{v:.1f}',va='center',fontsize=8)
    for i,row in n.iterrows():
        pos=nets.index(row.network);axs[2].plot([row.mag_min,row.mag_max],[pos,pos],color='#CCD4DA',lw=1.5)
        axs[2].plot([row.mag_q10,row.mag_q90],[pos,pos],color='#176D86',lw=4);axs[2].plot(row.mag_median,pos,'o',color='#B65A27',ms=4)
    axs[2].set_yticks(y,n.network.str.upper());axs[2].invert_yaxis();axs[2].set_xlabel('Magnitude (mixed reported scales)')
    for ax in axs:ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    finish(fig,'01_network_census','Network volume, observed automatic history and magnitude coverage',
      'All cohort events, grouped by preferred origin network. Automatic percentage uses events with downloaded history. Magnitude ranges show min–max (light), 10th–90th percentiles (thick) and median (dot). Different magnitude scales and completeness thresholds prevent direct sensitivity rankings. Source: network_summary.csv.')
    fig,axs=plt.subplots(3,5,figsize=(14,8),sharex=True,sharey=False)
    bins=np.arange(-2,8.5,.25)
    for ax,net in zip(axs.flat,nets):
        d=c[c.network.eq(net)];ax.hist(d.mag.dropna(),bins=bins,color=colors[net],edgecolor='white',lw=.25)
        ax.set_title(f'{net.upper()}  n={len(d):,}',loc='left',fontsize=10);ax.set_xlim(-2,8);ax.grid(axis='y',alpha=.15)
    for ax in axs[-1]:ax.set_xlabel('Magnitude')
    for ax in axs[:,0]:ax.set_ylabel('Events')
    finish(fig,'02_magnitude_distributions','Magnitude distributions differ strongly among network catalogs',
       'Quarter-magnitude histograms use independent y-axis ranges to retain shape. All magnitudes and event counts are catalog preferred values. Magnitude scales are mixed within and across panels. Source: catalog.csv.')
    fig,axs=plt.subplots(1,2,figsize=(14,6.5),gridspec_kw={'width_ratios':[1,1.7]})
    cov=[]
    for net in nets:
        a=n.set_index('network').loc[net];d=m[m.network.eq(net)];cov.append({'network':net,
          'History':100*a.history_available/a.events,'Reviewed':100*a.reviewed_events/a.events,'Phases':100*a.matched_phase_events/a.events,
          'Paired':100*a.automatic_reviewed_pairs/a.events,'Time σ':100*d.time_error_s.notna().sum()/a.events,
          'Horiz. σ':100*d.horizontal_error_km.notna().sum()/a.events,'Mag. σ':100*d.mag_error.notna().sum()/a.events})
    cov=pd.DataFrame(cov).set_index('network');cov.to_csv(OUT/'coverage_percentages.csv')
    im=heat(axs[0],cov,nets,list(cov.columns),'Coverage of requested measurements (%)',fmt='.0f',vmin=0,vmax=100)
    w=pd.read_csv(OUT/'weekly_automatic_coverage.csv');mat=w.pivot(index='network',columns='week',values='observed_automatic_percent')
    im=heat(axs[1],mat,nets,list(mat.columns),'Retained automatic history by event week (%)',fmt='.0f',vmin=0,vmax=100)
    fig.colorbar(im,ax=axs,shrink=.6,pad=.02,label='Events (%)')
    finish(fig,'03_coverage','Coverage and automatic-history availability accompany every comparison',
      'Coverage percentages use the full network cohort as denominator, including unreviewed events. Weekly automatic fractions use successfully downloaded histories. Missing uncertainty fields are unavailable, not zero. Phase products must match the reviewed origin ID. Source: coverage_percentages.csv and weekly_automatic_coverage.csv.')
    fig,axs=plt.subplots(1,4,figsize=(15,6.5))
    for ax,metric,label in zip(axs,['epicentral_shift_km','abs_delta_depth_km','abs_delta_time_s','abs_delta_mag_same_type'],
        ['Epicentral revision (km)','Absolute depth revision (km)','Absolute time revision (s)','Absolute magnitude revision\n(same magnitude type)']):
        intervals(ax,rs,metric,nets,label,log=metric!='abs_delta_mag_same_type')
    finish(fig,'04_automatic_revisions','Automatic-to-reviewed changes span different scales across networks',
      'Dots show median and horizontal spans the 10th–90th percentiles, with available n at right. Primary pair is earliest retained automatic versus latest reviewed origin from the same source and code. Spatial/time axes use symmetric log scaling near zero. These are revisions, not accuracy estimates. Magnitude comparisons require identical types. Source: revision_summary_long.csv.')
    fig,axs=plt.subplots(1,2,figsize=(14,6.5))
    pm=pd.read_csv(OUT/'revision_by_magnitude.csv')
    for ax,metric,title in zip(axs,['epicentral_shift_km','abs_delta_mag_same_type'],['Median epicentral revision (km)','Median absolute magnitude revision']):
        d=pm[pm.metric.eq(metric)].copy();d.loc[d.n<20,'median']=np.nan
        mat=d.pivot(index='network',columns='mag_bin',values='median');im=heat(ax,mat,nets,LABELS,title,fmt='.2f',cmap='YlOrRd')
        fig.colorbar(im,ax=ax,shrink=.7,pad=.08)
    finish(fig,'05_revisions_by_magnitude','Magnitude strata expose variation in revision size',
      'Cells show median paired revisions by reviewed magnitude. Cells with n<20 or unavailable data are blank. Magnitude revisions retain identical magnitude types only. Full n and quantiles, including hidden cells, are published. Source: revision_by_magnitude.csv.')
    fig,axs=plt.subplots(1,4,figsize=(15,6.5))
    for ax,metric,label in zip(axs,['associated_pick_count','num_phases_used','gap_deg','minimum_distance_km'],
      ['Associated picks','Reported used phases','Azimuthal gap (degrees)','Minimum station distance (km)']):intervals(ax,r,metric,nets,label,log=metric=='minimum_distance_km')
    finish(fig,'06_reviewed_geometry','Reviewed origins differ in phase support and network geometry',
      'Medians and 10th–90th percentile event spreads, with metric-specific n. Associated counts join reviewed-origin arrivals to picks. Used-phase counts come from origin product metadata and can follow provider-specific conventions. Minimum distance is reported epicentral distance converted from degrees. Source: reviewed_summary_long.csv.')
    fig,axs=plt.subplots(1,3,figsize=(14,6.5))
    for ax,metric,label in zip(axs,['P_count','S_count','P_S_ratio'],['Associated P picks','Associated S picks','P/S ratio (S>0 events)']):intervals(ax,r,metric,nets,label,log=metric=='P_S_ratio')
    finish(fig,'07_phase_balance','P and S support vary among reviewed network solutions',
      'P and S families follow the first letter of the case-insensitive reported arrival phase. P/S is an event-level ratio. Events with S=0 have undefined P/S and are counted separately in network_summary.csv. Dots and spans represent median and 10th–90th percentile spread. Source: reviewed_summary_long.csv.')
    for used,stem,sub in [('', '08_local_picks','Associated'),('used_','09_local_used_picks','Explicitly used')]:
        fig,axs=plt.subplots(1,2,figsize=(12,6.5))
        for ax,fam in zip(axs,['P','S']):
            rows=[]
            for net in nets:
                row={'network':net}
                for radius in [10,20,30]:
                    d=r[r.network.eq(net)&r.metric.eq(f'{fam}_{used}within_{radius}_km')]
                    row[f'≤{radius} km']=d['median'].iloc[0] if len(d) else np.nan
                rows.append(row)
            mat=pd.DataFrame(rows).set_index('network');im=heat(ax,mat,nets,['≤10 km','≤20 km','≤30 km'],f'{fam} picks: median per reviewed event',fmt='.1f',cmap='YlGnBu')
            fig.colorbar(im,ax=ax,shrink=.7,pad=.04)
        finish(fig,stem,f'{sub} local phase support within 10, 20 and 30 km',
          f'{sub} P and S arrival counts within inclusive epicentral distance thresholds. These are pick counts, not unique stations. An event with phase data and no qualifying local arrivals contributes zero. Missing distances cannot qualify and are reported in the coverage report. Explicitly used means positive time weight or timeUsed=true. Source: reviewed_summary_long.csv and reviewed_event_metrics.csv.gz.')
    fig,axs=plt.subplots(1,3,figsize=(14,6.5))
    for ax,metric,label in zip(axs,['P_polarity_fraction','automatic_fraction_known','known_mode_fraction'],
       ['P picks with marked polarity\n(event fraction)','Automatic picks / known-mode picks\n(event fraction)','Picks with known evaluation mode\n(event fraction)']):
        intervals(ax,r,metric,nets,label);ax.set_xlim(-.03,1.08)
    finish(fig,'10_polarity_automation','Polarity coverage and exported pick modes require separate denominators',
      'Medians and 10th–90th percentile event spreads. Marked polarity means positive or negative, divided by associated P picks. Automatic fraction uses only explicitly automatic or manual modes. The third panel shows whether that denominator covers the available picks. Unknown mode does not mean manual. Source: reviewed_summary_long.csv. Pick-weighted fractions also appear in network_summary.csv.')
    fig,axs=plt.subplots(1,4,figsize=(15,6.5))
    for ax,metric,label in zip(axs,['horizontal_error_km','depth_error_km','time_error_s','mag_error'],
      ['Reported horizontal uncertainty (km)','Reported depth uncertainty (km)','Reported origin-time uncertainty (s)','Reported magnitude uncertainty']):
        intervals(ax,r,metric,nets,label,log=metric!='mag_error')
    finish(fig,'11_reviewed_uncertainty','Reported uncertainty distributions reflect different provider conventions',
      'Medians and 10th–90th percentile spreads of available values. Confidence level, fixed-parameter handling and calculation method can differ across networks. Zero is retained as reported and does not prove perfect constraint. These fields are not a calibrated shared accuracy scale. Source: reviewed_summary_long.csv.')
    fig,axs=plt.subplots(2,2,figsize=(13,10))
    for ax,base,label in zip(axs.flat,['horizontal_error_km','depth_error_km','time_error_s','mag_error'],['Horizontal uncertainty (km)','Depth uncertainty (km)','Time uncertainty (s)','Magnitude uncertainty']):
        for offset,stage,color in [(-.12,'automatic','#B65A27'),(.12,'reviewed','#176D86')]:
            d=rs[rs.metric.eq(f'{stage}_{base}')].set_index('network').reindex(nets)
            ax.plot(d['median'],np.arange(len(nets))+offset,'o',color=color,label=stage.title(),ms=4)
        ax.set_yticks(range(len(nets)),[x.upper() for x in nets]);ax.invert_yaxis();ax.set_xlabel(label);ax.grid(axis='x',alpha=.2)
        if base!='mag_error':ax.set_xscale('symlog',linthresh=.1)
    axs[0,0].legend(loc='lower right')
    finish(fig,'12_paired_uncertainties','Automatic and reviewed uncertainty fields change within paired events',
      'Points show stage-specific medians in the paired cohort. Field-specific availability can differ between stages, so matched uncertainty deltas and n are also published in revision_summary_long.csv. Field conventions differ by network. Source: automatic_to_reviewed.csv.')
    mm=pd.read_csv(OUT/'reviewed_by_magnitude.csv')
    for stem,metrics,titles in [('13_support_by_magnitude',['associated_pick_count','P_S_ratio','gap_deg','minimum_distance_km'],
          ['Associated picks','P/S ratio','Azimuthal gap (degrees)','Minimum station distance (km)']),
        ('14_uncertainty_by_magnitude',['horizontal_error_km','depth_error_km','P_polarity_fraction','automatic_fraction_known'],
          ['Horizontal uncertainty (km)','Depth uncertainty (km)','P polarity fraction','Automatic / known-mode picks'])]:
        fig,axs=plt.subplots(2,2,figsize=(14,9))
        for ax,metric,title in zip(axs.flat,metrics,titles):
            for net in nets:
                d=mm[mm.metric.eq(metric)&mm.network.eq(net)].set_index('mag_bin').reindex(LABELS)
                med=d['median'].where(d.n.ge(20));ax.plot(range(len(LABELS)),med,'o-',label=net.upper(),color=colors[net],ms=3,lw=1.2)
            ax.set_xticks(range(len(LABELS)),LABELS);ax.set_title(title,loc='left',fontsize=11);ax.grid(alpha=.2)
            if metric in ('P_S_ratio','minimum_distance_km','horizontal_error_km','depth_error_km'):ax.set_yscale('symlog',linthresh=.1)
        handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=8,loc='lower center',frameon=False)
        finish(fig,stem,'Reviewed solution metrics across magnitude strata',
          'Lines join network medians within reviewed magnitude bins. Values require n≥20 for each metric and bin. No extrapolation or common completeness threshold is assumed. Full quantiles, n and missingness remain in CSV. Source: reviewed_by_magnitude.csv.')
    fig,ax=plt.subplots(figsize=(14,6))
    for net in nets:
        d=c[c.network.eq(net)];ax.scatter(d.longitude,d.latitude,s=np.clip((d.mag.fillna(0)+2)**2,2,75),alpha=.45,c=[colors[net]],label=f'{net.upper()} ({len(d):,})',linewidths=0,rasterized=True)
    ax.set_xlim(-180,180);ax.set_ylim(-85,85);ax.set_xticks(np.arange(-180,181,60));ax.set_yticks(np.arange(-60,61,30));ax.set_xlabel('Longitude (degrees)');ax.set_ylabel('Latitude (degrees)');ax.grid(alpha=.2)
    ax.legend(ncol=5,loc='upper center',bbox_to_anchor=(.5,-.16),frameon=False,markerscale=1.2)
    finish(fig,'15_geographic_distribution','Network cohorts cover different earthquake populations',
      'All catalog epicenters on a longitude–latitude coordinate plot. Colors identify the preferred origin network and marker area grows with reported magnitude. No basemap or area-preserving projection is implied. Geography and depth confound network quality comparisons. Source: catalog.csv.')
    cs=pd.read_csv(OUT/'cross_network_summary.csv')
    if len(cs):
        d=cs[cs.metric.eq('epicentral_shift_km')].sort_values('n',ascending=False).head(20)
        fig,ax=plt.subplots(figsize=(10,7));ys=np.arange(len(d))
        ax.hlines(ys,d.q10,d.q90,color='#176D86',lw=2);ax.plot(d['median'],ys,'o',color='#B65A27')
        ax.set_yticks(ys,[f"{a.upper()} vs {b.upper()}  (n={int(z):,})" for a,b,z in zip(d.network,d.reference_network,d.n)]);ax.invert_yaxis();ax.set_xscale('symlog',linthresh=.1);ax.set_xlabel('Epicentral separation (km)');ax.grid(axis='x',alpha=.2)
        finish(fig,'16_cross_network','Overlapping reviewed origins permit a separate within-event comparison',
          'Up to 20 most populated ordered network pairs. Each other network reviewed origin is compared with the same event’s preferred-network reviewed reference. Dots and spans show median and 10th–90th percentiles. Events can enter more than one pair. These selected overlaps do not establish which origin is accurate. Source: cross_network_summary.csv.')
    (FIG/'captions.json').write_text(json.dumps(CAPTIONS,indent=2),encoding='utf-8')
    (FIG/'README.md').write_text('# Figure captions\n\n'+'\n\n'.join(f"## {k}: {v['title']}\n\n{v['caption']}" for k,v in CAPTIONS.items()),encoding='utf-8')
    print('Created',len(CAPTIONS),'publication figures in PDF, SVG and PNG',flush=True)

if __name__=='__main__':main()
