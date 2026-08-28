# Full corpus and retrieval-readiness audit

## Verdict

**Passed and ready for a controlled Cloudflare staging build.** The canonical corpus is high quality and unusually well evidenced. I found one narrow active text-corruption class, repaired it from preserved official evidence, and found no remaining blocking error in canonical text structure, identifiers, hashes, provenance binding, derived artifacts, or the prepared ingestion layer.

Quality assessment:

- Canonical corpus engineering: **9.4/10**
- Provenance and reproducibility: **9.5/10**
- Authority-aware retrieval design: **9.4/10**
- Pre-repair embedding readiness: **7.8/10** because 73 records required safe subdivision
- Final ingestion readiness: **9.6/10**

These scores evaluate engineering fitness, not an assertion that every historical source edition or theological interpretation is exhaustive.

## Independent results

| Gate | Result |
|---|---:|
| Canonical documents | 108 |
| Canonical records | 13,725 |
| Words | 1,914,116 |
| Canonical errors after repair | 0 |
| Raw/provenance hash failures | 0 |
| Derived-artifact relationship errors | 0 |
| Fidelity sample | 687 (5.005%) |
| Fidelity failures | 0 |
| Retrieval chunks | 13,828 |
| Lossless chunk reconstruction failures | 0 |
| Ingestion validation errors | 0 |
| Local D1/SQLite `quick_check` | `ok` |

## Surgical repairs

### Source text

The legacy mirror for *Dignitas Personae* contained U+001A followed by a stray `c` in paragraphs 8 and 34. The preserved Holy See verification text independently showed ellipses at both positions. I replaced only the asserted corrupt sequences, recalculated both record hashes and the DP canonical/provenance hashes, and logged the exact repair in `AUDIT_CORRECTIONS.json`.

### Validator portability

The supplied standalone validator hard-coded a Manus/Kimi build path and accepted only simple English IDs. I changed it to resolve the corpus relative to the release by default, accept `--corpus-root`, and validate the corpus's actual hierarchical bilingual ID grammar. It now runs independently outside the original agent environment.

### Retrieval taxonomy

Most doctrinal-dicastery records use canonical source family `dicastery`; one historical expansion set uses `doctrinal_dicastery`. Both share authority class `dicastery_doctrinal`. Canonical values were retained for source fidelity. Retrieval metadata maps both to `dicastery` while retaining `source_family_canonical`, eliminating a filter split without rewriting provenance.

### Oversized records

The largest canonical unit was 5,196 words. Canonical records remain unchanged, but 73 units are split at preferred paragraph or sentence boundaries into deterministic chunks capped at 900 words. Reconstruction is byte-for-byte lossless; adjacent chunk links replace blind overlap.

## Non-errors retained deliberately

- `mag:CPG:closing:en` and `mag:IND:p39:en` are legitimate signature units.
- “subscribe to” in *Caritas in Veritate* 46 and “cookies” in *Dilexit Nos* 7 are source content, not web boilerplate.
- CCC 1786 and 1799 contain an exact repeated English passage in the source.
- Ancient council dates sometimes have only year or year-range precision; no artificial day was invented.
- Florence, Lyons II, Trent, and several ancient-council files legitimately vary title, date, or unit type within a grouped document family.
- Compendium question 39 preserves the official source's malformed display `2112-213` while using the separately evidenced normalized CCC references 212-213 for retrieval.

## Documented limitations

The frozen evidence gate classifies 16 of 687 sampled records as documented limitations rather than source-fidelity failures. These cover known source-access, note-attachment, transcription, or edition constraints already disclosed in provenance. They should remain visible and must not be silently “repaired” without new source evidence.

This corpus is broad but not a substitute for live official authority on current canon law, present discipline, later documents, changed editions, or current institutional facts. Existing Exa/Firecrawl official-source fallback must remain available.

## Cloudflare compatibility

The prepared 1,024-dimensional BGE-M3 contract fits Vectorize's current dimensional ceiling. Generated vector IDs are 43 bytes, below the 64-byte limit, and metadata is at most 287 bytes, far below the 10 KiB per-vector limit. The D1 import is below Cloudflare's current 5 GiB file-import limit, and each insert is kept below the current 100 KiB SQL-statement limit.

No Cloudflare mutation occurred during this audit. Resource creation, embedding, staging integration, evaluation, and production promotion remain for the next authorized session.
