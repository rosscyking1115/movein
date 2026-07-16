# Maintenance policy

England & Wales Housing Decision Support is a completed portfolio reference
implementation. It has no active product or feature roadmap.

Changes are accepted when they address one of these maintenance needs:

- an upstream official/open-data source changes or becomes unavailable;
- a security issue or supported dependency requires an update;
- a correctness defect is found in ingestion, modelling, scoring, API behaviour,
  or the website's representation of the evidence;
- tests, documentation, source provenance, or deployed evidence need to be kept
  aligned with what is actually built.

New product surfaces, speculative indicators, and expansion beyond England and
Wales are outside the current scope. Any future expansion must first define its
source coverage, uncertainty rules, versioned contract, and regression evidence.

The non-negotiable publication rules remain: indicators are not verdicts; scores
are never encoded as red/amber/green judgements; each score stays beside its
source fact; uncertainty and unsupported jurisdictions are explicit; outputs are
area-level rather than property valuations; and public area names are human-readable.
