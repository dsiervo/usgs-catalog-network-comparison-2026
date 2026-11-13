# Figure captions

## 01_network_census: Network volume, observed automatic history and magnitude coverage

All cohort events, grouped by preferred origin network. Automatic percentage uses events with downloaded history. Magnitude ranges show min–max (light), 10th–90th percentiles (thick) and median (dot). Different magnitude scales and completeness thresholds prevent direct sensitivity rankings. Source: network_summary.csv.

## 02_magnitude_distributions: Magnitude distributions differ strongly among network catalogs

Quarter-magnitude histograms use independent y-axis ranges to retain shape. All magnitudes and event counts are catalog preferred values. Magnitude scales are mixed within and across panels. Source: catalog.csv.

## 03_coverage: Coverage and automatic-history availability accompany every comparison

Coverage percentages use the full network cohort as denominator, including unreviewed events. Weekly automatic fractions use successfully downloaded histories. Missing uncertainty fields are unavailable, not zero. Phase products must match the reviewed origin ID. Source: coverage_percentages.csv and weekly_automatic_coverage.csv.

## 04_automatic_revisions: Automatic-to-reviewed changes span different scales across networks

Dots show median and horizontal spans the 10th–90th percentiles, with available n at right. Primary pair is earliest retained automatic versus latest reviewed origin from the same source and code. Spatial/time axes use symmetric log scaling near zero. These are revisions, not accuracy estimates. Magnitude comparisons require identical types. Source: revision_summary_long.csv.

## 05_revisions_by_magnitude: Magnitude strata expose variation in revision size

Cells show median paired revisions by reviewed magnitude. Cells with n<20 or unavailable data are blank. Magnitude revisions retain identical magnitude types only. Full n and quantiles, including hidden cells, are published. Source: revision_by_magnitude.csv.

## 06_reviewed_geometry: Reviewed origins differ in phase support and network geometry

Medians and 10th–90th percentile event spreads, with metric-specific n. Associated counts join reviewed-origin arrivals to picks. Used-phase counts come from origin product metadata and can follow provider-specific conventions. Minimum distance is reported epicentral distance converted from degrees. Source: reviewed_summary_long.csv.

## 07_phase_balance: P and S support vary among reviewed network solutions

P and S families follow the first letter of the case-insensitive reported arrival phase. P/S is an event-level ratio. Events with S=0 have undefined P/S and are counted separately in network_summary.csv. Dots and spans represent median and 10th–90th percentile spread. Source: reviewed_summary_long.csv.

## 08_local_picks: Associated local phase support within 10, 20 and 30 km

Associated P and S arrival counts within inclusive epicentral distance thresholds. These are pick counts, not unique stations. An event with phase data and no qualifying local arrivals contributes zero. Missing distances cannot qualify and are reported in the coverage report. Explicitly used means positive time weight or timeUsed=true. Source: reviewed_summary_long.csv and reviewed_event_metrics.csv.gz.

## 09_local_used_picks: Explicitly used local phase support within 10, 20 and 30 km

Explicitly used P and S arrival counts within inclusive epicentral distance thresholds. These are pick counts, not unique stations. An event with phase data and no qualifying local arrivals contributes zero. Missing distances cannot qualify and are reported in the coverage report. Explicitly used means positive time weight or timeUsed=true. Source: reviewed_summary_long.csv and reviewed_event_metrics.csv.gz.

## 10_polarity_automation: Polarity coverage and exported pick modes require separate denominators

Medians and 10th–90th percentile event spreads. Marked polarity means positive or negative, divided by associated P picks. Automatic fraction uses only explicitly automatic or manual modes. The third panel shows whether that denominator covers the available picks. Unknown mode does not mean manual. Source: reviewed_summary_long.csv. Pick-weighted fractions also appear in network_summary.csv.

## 11_reviewed_uncertainty: Reported uncertainty distributions reflect different provider conventions

Medians and 10th–90th percentile spreads of available values. Confidence level, fixed-parameter handling and calculation method can differ across networks. Zero is retained as reported and does not prove perfect constraint. These fields are not a calibrated shared accuracy scale. Source: reviewed_summary_long.csv.

## 12_paired_uncertainties: Automatic and reviewed uncertainty fields change within paired events

Points show stage-specific medians in the paired cohort. Field-specific availability can differ between stages, so matched uncertainty deltas and n are also published in revision_summary_long.csv. Field conventions differ by network. Source: automatic_to_reviewed.csv.

## 13_support_by_magnitude: Reviewed solution metrics across magnitude strata

Lines join network medians within reviewed magnitude bins. Values require n≥20 for each metric and bin. No extrapolation or common completeness threshold is assumed. Full quantiles, n and missingness remain in CSV. Source: reviewed_by_magnitude.csv.

## 14_uncertainty_by_magnitude: Reviewed solution metrics across magnitude strata

Lines join network medians within reviewed magnitude bins. Values require n≥20 for each metric and bin. No extrapolation or common completeness threshold is assumed. Full quantiles, n and missingness remain in CSV. Source: reviewed_by_magnitude.csv.

## 15_geographic_distribution: Network cohorts cover different earthquake populations

All catalog epicenters on a longitude–latitude coordinate plot. Colors identify the preferred origin network and marker area grows with reported magnitude. No basemap or area-preserving projection is implied. Geography and depth confound network quality comparisons. Source: catalog.csv.

## 16_cross_network: Overlapping reviewed origins permit a separate within-event comparison

Up to 20 most populated ordered network pairs. Each other network reviewed origin is compared with the same event’s preferred-network reviewed reference. Dots and spans show median and 10th–90th percentiles. Events can enter more than one pair. These selected overlaps do not establish which origin is accurate. Source: cross_network_summary.csv.