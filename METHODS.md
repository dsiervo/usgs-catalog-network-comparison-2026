# Methods and interpretation

## Cohort and network attribution

The study includes every ComCat record classified as an earthquake with preferred origin time in the half-open interval 2026-08-11 to 2026-11-11 UTC, worldwide, without a magnitude threshold. This is the preceding three calendar months relative to November 11, using complete UTC days. Weekly queries avoid the 20,000-result API ceiling. Boundary duplicates are removed by ComCat event ID. Query metadata and retrieval time are preserved. Records deleted before cohort retrieval are outside the cohort, so automatic false-positive/deletion rates cannot be estimated.

The primary comparison groups each earthquake by the preferred origin network (`net` in the catalog). This is an operational proxy for the authoritative network, not an independent reconstruction of authoritative geographic polygons. ComCat preferences depend on authority, source and update time. Some sources have no preferred events but contribute solutions. `network_contributions.csv` therefore separately counts each unique earthquake with any retained origin from each network. These overlapping counts must not be added to obtain a catalog total. Product publisher and origin author are preserved separately.

## Version selection and automatic publication

The primary acquisition uses the documented ComCat PDL archive `products_created_after` endpoint in batches of 1,000 notifications, beginning one UTC day before the cohort. Full origin and phase-data metadata are retained through a fixed retrieval cutoff. This bulk route greatly reduces requests relative to separate event-detail queries. ComCat alias IDs from the cohort link archived products to events. Cached pilot event-detail queries use `includesuperseded=true` and are merged by product ID. Only UPDATE origin versions enter the analysis. `review-status=automatic` provides direct evidence of an automatic submission. Absence of such a retained version does not establish that a network never sends automatic events. Raw archive responses and pilot detail responses remain available for provenance. A network's history coverage and observed automatic-event count accompany every percentage. The realtime east PDL hub is not used for the three-month history because its retained period is shorter than the cohort.

For each event, choose the latest reviewed origin from its preferred origin network as the reviewed reference. Pair it with the earliest retained automatic origin from the **same network and product code**, strictly preceding the reviewed update. `last_automatic_to_reviewed.csv` repeats the comparison with the latest preceding automatic origin as a sensitivity analysis. Events without a pair remain in the cohort and coverage tables. The reviewed reference is the latest available at retrieval, rather than a guaranteed final catalog solution.

Signed changes are reviewed minus automatic. Epicentral separation uses the WGS84 inverse geodesic. Depth and origin-time changes remain separate. Magnitude changes compare identical magnitude-type strings only in the main summaries. Type changes are counted and full values retained. Reported uncertainties are compared for the same paired events, using USGS product properties in km, seconds, or magnitude units. Different confidence levels, error definitions, fixed depths and velocity models can prevent physical comparisons across providers. We retain QuakeML confidence metadata and do not pool them into a calibrated common error scale. Revisions are not errors against independent ground truth. Review latency uses product update times only and should not be interpreted as analyst working time.

## Reviewed pick metrics

Download a reviewed `phase-data` product whose QuakeML origin ID exactly matches the selected reviewed origin. Within its QuakeML file, select that exact origin ID, then join its arrival `pickID` references to pick objects. Only those associated picks enter the main count, deduplicated by pick ID. Unassociated picks in the document do not enter counts. Unresolved references and origin-ID mismatches are reported explicitly.

- **Associated picks:** distinct referenced pick IDs, regardless of location weight. **Used picks:** explicit positive `timeWeight`, or explicit `timeUsed=true` where weight is absent. Missing usage metadata remains unknown. The provider's `usedPhaseCount` and product phase count are retained independently because reporting conventions can differ.
- **P/S:** phases whose case-insensitive names start with P or S, including regional suffixes. Other phase families remain outside both counts. P/S is P divided by S per event. Zero-S events have an undefined ratio and receive a separate count. This operational phase-family definition is recorded rather than presented as a full ray-path taxonomy.
- **Local picks:** arrival distance is epicentral distance in degrees. Convert with mean Earth radius 6,371.0088 km (111.19508 km/degree). Thresholds are inclusive at 10, 20 and 30 km. Counts represent observations, not unique stations. Associated and explicitly used versions are both published. Missing distances remain unavailable and their counts are reported.
- **Azimuthal gap and nearest station:** use the selected origin's reported properties, not all stations in the XML. Minimum station distance is converted from degrees to km. Preserve XML quality fields as a cross-reference.
- **P polarity fraction:** P picks explicitly marked positive or negative divided by all associated P picks. Undecidable and missing polarities do not enter the numerator. This measures encoded polarity coverage, not focal mechanism quality or polarity correctness.
- **Automatic picks in reviewed origins:** count only explicit `evaluationMode=automatic`. Publish automatic/(automatic+manual), automatic/all associated picks, and the fraction with known modes. Unknown modes cannot establish manual measurement. Explicit mode reflects the exported record and need not capture every human edit or review in the network's processing system.

## Descriptive comparisons and magnitude strata

Magnitude bins are M<0, [0,1), [1,2), [2,3), [3,4), [4,5), and M≥5. Preferred catalog magnitude bins characterize submitted event counts. Reviewed magnitude bins characterize manual solution metrics and paired revisions. Main displays show medians with 10th–90th percentile spreads, **not confidence intervals**. Full summaries include n, missing count, mean, quartiles and 95th percentile. Cells with fewer than 20 observations are hidden in magnitude-comparison figures, while all values remain in CSV outputs. Pick-weighted aggregate fractions and event-level fractions have separate denominators.

Networks observe different regions, depths, magnitude types and detectability thresholds. Matching magnitude bins helps describe these differences but does not remove this confounding. Do not rank intrinsic network accuracy from these observational summaries. Cross-network comparisons of the same ComCat event are provided separately using the latest retained reviewed origin from another network against the preferred network's reviewed reference. These comparisons are selected overlaps, not independent ground truth.

## Reproduction

Run `python -m pip install -r requirements.txt`, `python acquire.py --catalog-only`, `python bulk_acquire.py`, `python analyze.py`, and `python figures.py`. Acquisition resumes cached downloads. The frozen snapshot is distributed in the GitHub release. Restoring its `.cache/` directories reproduces extraction without depending on subsequent ComCat changes. Every raw product URL and selected product ID is preserved. No unit tests or checksum/hash verification are used. `coverage_report.json` describes cohort reconciliation, parsing coverage, missingness and runtime versions. FDSN requests are paced below its published response limit of 500 requests per five minutes. Static product downloads and bulk metadata are paced separately.

## Primary sources

Retrieved November 11, 2026:

1. [USGS FDSN event API](https://earthquake.usgs.gov/fdsnws/event/1/): query parameters, superseded products, preferred sources, nonimplemented arrivals parameter.
2. [ComCat products and preference](https://earthquake.usgs.gov/data/catalog/products.php): source/type/code/update identity and authoritative preference.
3. [USGS product types](https://earthquake.usgs.gov/data/products/): origin and phase-data definitions.
4. [Catalog roster](https://earthquake.usgs.gov/data/catalog/catalogs/) and [contributor roster](https://earthquake.usgs.gov/data/catalog/contributors/): provider identities and scope.
5. [QuakeML BED 1.2 specification](https://quake.ethz.ch/quakeml/docs/REC?action=AttachFile&do=get&target=QuakeML-BED-20130214b.pdf): sections 3.3.8, 3.4.1, 3.5.3, 3.5.4, 3.5.10 and 3.5.11 define origin quality, evaluation mode, arrival distance, weights and picks.
6. [USGS explanation of depth references](https://www.usgs.gov/faqs/what-does-it-mean-earthquake-occurred-a-depth-0-km-how-can-earthquake-have-a-negative-depth): network-dependent depth reference and depth resolution.
7. [PDL Products Created After Client](https://ghsc.code-pages.usgs.gov/hazdev/pdl/userguide/receiving/products-created-after-client.html): documented archive batch endpoint and cursor semantics. Archive records carry product metadata, content URLs and source/type/code/update identity.
