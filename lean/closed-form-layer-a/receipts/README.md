# Receipt provenance

These are retained historical records, not new executions of the cloud proof.
All paths in the public copies are relative to the bundle root. No private
machine or account identifiers are retained. Source and dependency hashes,
timing fields and results are not rewritten. Log paths in historical TSVs
refer to the original runner's `BUILD.step7-state/logs/` directory; individual
module logs are not included. They are populated by a new verification run.

- `BUILD.step7-cloud.tsv`: initial 1,083-entry cloud structural run.
- `cloud-BUILD.step7-cloud.tsv`: cumulative cloud history, including those same
  1,083 entries and 226 follow-up entries. Do not add the two files together.
- `cloud-BUILD.step7-final-files.tsv`: final local I01/I04 structural samples
  copied back with the cloud directory; these are laptop timings, not cloud timings.
- `cloud-BUILD.step7-measure.tsv`: historical local measurements, including six
  failed development entries and later saving samples.
- `cloud-BUILD.step9-final-files.tsv`: final local saving samples and two shared
  prerequisites; despite the filename prefix these are laptop timings.
- `BUILD.step7-cloud-run.log`, `BUILD.step9-cloud-run.log`: recorded scheduling,
  results and the final printed audit reports. The latter has 1,013 SKIP entries.
- `BUILD.step7-cloud-axioms.log`: initial structural provider audit.
- `BUILD.step9-cloud-axioms.log`: complete final five-theorem production audit;
  the main theorem line is copied verbatim into `expected/axioms.txt`.
- `unsplit-I01.json`: the failed 600.03-second benchmark. The reported wrapper
  RSS is not a measurement of Lean peak memory.
- `local-I01-assembly.json`: earlier 42.155-second I01 assembly measurement;
  the private absolute compiler command has been omitted.
- `development-runs.tsv`: retained individual development run outcomes projected
  from measurement JSON files; command paths are omitted. This is not a claim
  that every past command had a retained measurement record.
- `bundle-statement*.json` and `.log`: the failed formatting attempt and successful
  statement extraction during packaging. Compiler commands use the tool name
  and query basename in place of private installation and working paths. Their
  axiom reports concern the default placeholder graph, not the production proof.

SHA-256 checksums of these public receipt bytes are in `receipts.sha256` at the
bundle root. Hashes in the TSVs are hashes recorded at execution time; the latest
source hash for each production module matches the staged source. Superseded
local sample source hashes describe their historical revisions.
