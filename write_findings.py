"""Write the research findings directly from final summary tables."""
import json
import pandas as pd
from pathlib import Path
R=Path(__file__).resolve().parent
n=pd.read_csv(R/'results/network_summary.csv')
r=pd.read_csv(R/'results/revision_summary_long.csv')
a=json.loads((R/'results/coverage_report.json').read_text())
lines=['# U.S. authoritative regional network comparison','',
 'Study interval: August 11 through November 10, 2026 UTC. The final cohort uses only the 12 regional network codes in the official USGS ANSS authoritative-region layer. NEIC worldwide reporting, AVO and Montana are outside this comparison. Offshore and border events reported preferentially by these networks remain included.','',
 f"The cohort contains **{a['catalog_events']:,} earthquakes**, with **{a['reviewed_events']:,} reviewed origins**, **{a['phase_status_counts']['ok']:,} matching reviewed phase files**, and **{a['automatic_reviewed_pairs']:,} automatic-to-reviewed pairs**. All cohort events have downloaded product history. There are {a['phase_status_counts'].get('no_matching_reviewed_phase_product',0)} reviewed origins without a matching phase product.",'',
 f"**{int(n.observed_automatic_events.gt(0).sum())} networks** have retained automatic-origin submissions in this cohort. Absence of a retained automatic version cannot establish that a network never publishes automatically. The primary pair compares the earliest automatic with the latest reviewed origin from the same network and product code.",'',
 '## Event submissions and magnitude ranges','',
 '| Network | Preferred events | Magnitude range | Observed automatic events | Paired revisions |','|---|---:|---:|---:|---:|']
for d in n.itertuples():lines.append(f'| {d.network.upper()} | {d.events:,} | {d.mag_min:.2f} to {d.mag_max:.2f} | {d.observed_automatic_events:,} | {d.automatic_reviewed_pairs:,} |')
lines+=['','Counts refer to preferred ComCat events, rather than the complete local catalogs. Magnitude scales, detection thresholds and geographic populations differ. Overlapping contributor counts are supplied separately and should not be summed.','',
 '## Automatic-to-reviewed revisions','',
 '| Network | Paired events | Median epicentral revision (km) | 90th percentile (km) | Median absolute same-type magnitude revision |','|---|---:|---:|---:|---:|']
for net in n.network:
    x=r[(r.network==net)&(r.metric=='epicentral_shift_km')]
    y=r[(r.network==net)&(r.metric=='abs_delta_mag_same_type')]
    if len(x) and x.iloc[0]['n']:
        z=x.iloc[0];v=y.iloc[0]['median'] if len(y) else float('nan')
        lines.append(f"| {net.upper()} | {int(z['n']):,} | {z['median']:.3f} | {z['q90']:.3f} | {v:.3f} |")
lines+=['','The eight Utah pairs provide very limited evidence. Revisions measure changes relative to review, not accuracy against independent ground truth. Magnitude type changes are excluded from like-for-like magnitude summaries. Origin time, depth, signed changes, reported uncertainties and latest-automatic sensitivity results are in the accompanying tables.','',
 '## Automatic picks and polarity','',
 '| Network | Automatic picks among known modes (%) | P picks with marked polarity (%) |','|---|---:|---:|']
for d in n.itertuples():lines.append(f'| {d.network.upper()} | {d.automatic_percent_known:.2f} | {d.polarity_percent_P:.2f} |')
lines+=['','These are pick-weighted fractions. Exported evaluation modes cover all associated picks in this snapshot. A reviewed origin may retain automatic picks. Zero encoded polarities indicate absent positive/negative markings in the selected phase files, not proof that analysts never examine first motion.','',
 '## Figures and data','',
 'The figures directory contains 16 scientific figures in PDF, SVG and 300-dpi PNG, with captions and source-table references. Comparisons cover phase support, P/S, local P and S observations at 10/20/30 km, explicitly used arrivals, gap, minimum distance, polarity, automatic pick modes, uncertainty and magnitude strata. Distribution spans show 10th–90th percentiles, not confidence intervals. Magnitude-bin displays suppress cells with fewer than 20 events.','',
 'Reported uncertainty conventions are not calibrated across networks. Review status, pick mode, phase usage and missing fields remain distinct. See METHODS.md for definitions and limitations.','',
 '[Frozen source archive](https://github.com/dsiervo/usgs-catalog-network-comparison-2026/releases/tag/snapshot-2026-11-11). The raw acquisition is broader than the final authoritative-network comparison. No unit tests or hash verification were used.']
(R/'FINDINGS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
