# U.S. authoritative regional network comparison

Study interval: August 11 through November 10, 2026 UTC. The final cohort uses only the 12 regional network codes in the official USGS ANSS authoritative-region layer. NEIC worldwide reporting, AVO and Montana are outside this comparison. Offshore and border events reported preferentially by these networks remain included.

The cohort contains **25,494 earthquakes**, with **21,580 reviewed origins**, **21,576 matching reviewed phase files**, and **9,754 automatic-to-reviewed pairs**. All cohort events have downloaded product history. There are 4 reviewed origins without a matching phase product.

**9 networks** have retained automatic-origin submissions in this cohort. Absence of a retained automatic version cannot establish that a network never publishes automatically. The primary pair compares the earliest automatic with the latest reviewed origin from the same network and product code.

## Event submissions and magnitude ranges

| Network | Preferred events | Magnitude range | Observed automatic events | Paired revisions |
|---|---:|---:|---:|---:|
| AK | 7,352 | 0.20 to 5.60 | 3,425 | 2,855 |
| NC | 5,266 | -0.33 to 4.96 | 3,835 | 1,156 |
| CI | 4,463 | -0.50 to 4.89 | 3,996 | 3,938 |
| TX | 2,600 | 0.10 to 4.00 | 666 | 666 |
| UU | 1,831 | -0.21 to 3.79 | 8 | 8 |
| HV | 1,409 | 0.51 to 5.20 | 1,290 | 750 |
| UW | 881 | -0.53 to 4.30 | 101 | 100 |
| PR | 836 | 0.69 to 4.80 | 0 | 0 |
| OK | 433 | 0.15 to 3.57 | 66 | 64 |
| NN | 309 | 1.26 to 4.10 | 281 | 217 |
| NM | 79 | 0.88 to 2.47 | 0 | 0 |
| SE | 35 | 1.49 to 2.54 | 0 | 0 |

Counts refer to preferred ComCat events, rather than the complete local catalogs. Magnitude scales, detection thresholds and geographic populations differ. Overlapping contributor counts are supplied separately and should not be summed.

## Automatic-to-reviewed revisions

| Network | Paired events | Median epicentral revision (km) | 90th percentile (km) | Median absolute same-type magnitude revision |
|---|---:|---:|---:|---:|
| AK | 2,855 | 1.901 | 6.688 | 0.200 |
| NC | 1,156 | 0.539 | 2.838 | 0.100 |
| CI | 3,938 | 0.357 | 1.731 | 0.131 |
| TX | 666 | 1.300 | 4.371 | 0.100 |
| UU | 8 | 0.812 | 1.199 | 0.030 |
| HV | 750 | 0.811 | 2.153 | 0.160 |
| UW | 100 | 0.636 | 2.649 | 0.182 |
| OK | 64 | 0.961 | 4.578 | 0.180 |
| NN | 217 | 2.441 | 25.776 | 0.090 |

The eight Utah pairs provide very limited evidence. Revisions measure changes relative to review, not accuracy against independent ground truth. Magnitude type changes are excluded from like-for-like magnitude summaries. Origin time, depth, signed changes, reported uncertainties and latest-automatic sensitivity results are in the accompanying tables.

## Automatic picks and polarity

| Network | Automatic picks among known modes (%) | P picks with marked polarity (%) |
|---|---:|---:|
| AK | 66.49 | 0.00 |
| NC | 1.25 | 64.72 |
| CI | 65.86 | 31.70 |
| TX | 0.02 | 12.89 |
| UU | 0.13 | 43.76 |
| HV | 0.09 | 76.53 |
| UW | 2.62 | 52.52 |
| PR | 0.10 | 97.21 |
| OK | 0.00 | 13.69 |
| NN | 0.00 | 0.00 |
| NM | 0.99 | 72.59 |
| SE | 0.00 | 55.45 |

These are pick-weighted fractions. Exported evaluation modes cover all associated picks in this snapshot. A reviewed origin may retain automatic picks. Zero encoded polarities indicate absent positive/negative markings in the selected phase files, not proof that analysts never examine first motion.

## Figures and data

The figures directory contains 16 scientific figures in PDF, SVG and 300-dpi PNG, with captions and source-table references. Comparisons cover phase support, P/S, local P and S observations at 10/20/30 km, explicitly used arrivals, gap, minimum distance, polarity, automatic pick modes, uncertainty and magnitude strata. Distribution spans show 10th–90th percentiles, not confidence intervals. Magnitude-bin displays suppress cells with fewer than 20 events.

Reported uncertainty conventions are not calibrated across networks. Review status, pick mode, phase usage and missing fields remain distinct. See METHODS.md for definitions and limitations.

[Frozen source archive](https://github.com/dsiervo/usgs-catalog-network-comparison-2026/releases/tag/snapshot-2026-11-11). The raw acquisition is broader than the final authoritative-network comparison. No unit tests or hash verification were used.
