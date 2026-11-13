# USGS ComCat network comparison

**Final comparison scope:** U.S. ANSS authoritative regional networks AK, CI, HV, NC, NM, NN, OK, PR, SE, TX, UU and UW, using the official USGS authoritative-region roster. Worldwide NEIC events and AV/MB contributors are excluded from the main results. The worldwide acquisition below is the source pool, not the comparison cohort.

Reproducible study of earthquakes with preferred origin times in **2026-08-11 00:00:00 UTC through 2026-11-11 00:00:00 UTC (exclusive)**. All magnitudes, worldwide, event type earthquake. Data retrieved beginning November 11, 2026.

## Research questions

- Event counts and magnitude distributions by preferred origin network and by contributing origin source.
- Evidence of automatic submissions in superseded origin products, with coverage denominators.
- Earliest automatic versus latest reviewed solution from the same network, including magnitude type changes, origin time, epicentral/depth shifts and reported uncertainties.
- Reviewed origins: associated/used picks, P/S ratio, P and S within 10/20/30 km, azimuthal gap, nearest station, P polarity coverage, and automatic pick retention.
- Comparisons within magnitude strata, with explicit missingness and observational limitations.

## Method commitments

Use USGS FDSN event queries and versioned PDL origin/phase-data products. Link arrivals to picks in the selected reviewed QuakeML origin. Unknown pick evaluation modes remain unknown. A reviewed origin does not imply manually measured picks. Retained automatic history establishes observed publication, not a complete audit of network operations. Changes relative to reviewed origins measure revision, not accuracy against independent ground truth.

No unit tests or checksum/hash verification are used. Acquisition has resumable caches and descriptive coverage/reconciliation reports. Code, outputs, and documentation are committed and pushed at each completed work stage. Large raw snapshots are distributed as repository release assets when needed.

## Primary references

- [USGS FDSN API](https://earthquake.usgs.gov/fdsnws/event/1/)
- [ComCat product versioning and preference](https://earthquake.usgs.gov/data/catalog/products.php)
- [ComCat overview](https://earthquake.usgs.gov/data/comcat/)

## Findings and deliverables

- [Research findings](FINDINGS.md): 25,494 events across 12 authoritative regional networks, with 9,754 automatic-to-reviewed pairs.
- [PowerPoint](presentation/output/usgs_authoritative_networks.pptx): 24 slides with editable charts.
- [Publication figures](figures/): 16 figures in PDF, SVG and 300-dpi PNG, with captions.
- [Comparison tables](results/): event metrics, magnitude strata, pick support, uncertainty and coverage.
- [Frozen source downloads](https://github.com/dsiervo/usgs-catalog-network-comparison-2026/releases/tag/snapshot-2026-11-11).

The source download covers a wider catalog than the final comparison. Final results include only the official ANSS regional-authority roster described in METHODS.md. The local PowerPoint replaces the unfinished cloud draft after presentation-service timeouts.
