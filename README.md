# Catholic Doctrine and Magisterium Canonical RAG Corpus

A validated, citation-preserving, authority-aware corpus of Catholic doctrinal sources prepared for retrieval-augmented generation, theological research, education, search, and citation-grounded Catholic AI.

This repository was prepared for [Theology AI](https://theologyai.net) by AD IPSUM and is released publicly for the service of the Church and the wider research community.

## What is included

- **108 canonical Church documents**
- **13,725 canonical records** and **1,914,116 source-text words**
- **10,102 English** records and **3,623 Latin** records
- **13,828 lossless retrieval chunks**, capped at 900 words
- **23,825 exact-locus aliases** for named paragraphs, canons, sessions, questions, and document references
- The current *Catechism of the Catholic Church*, including the 2018 revision of paragraph 2267
- The *Compendium of the Catechism*, with normalized CCC references for all 598 questions
- Ancient, medieval, Trent, Vatican I, and all sixteen Vatican II documents represented in the release inventory
- Papal and doctrinal-dicastery documents spanning dogmatic, moral, social, bioethical, ecumenical, and pastoral teaching
- Stable record and chunk IDs, canonical citations, source URLs, provenance, footnotes, and SHA-256 hashes
- Authority-aware metadata that distinguishes catechism, council, papal, and dicastery sources without flattening them into a simplistic “infallible” flag
- Exact, lexical, and dense-retrieval inputs
- D1/SQLite schema and deterministic import builder
- Cloudflare Vectorize-compatible embedding records, while remaining vendor-neutral
- No embeddings, vector database, credentials, or live deployment configuration

## Why this corpus exists

General-purpose language models can explain Catholic doctrine well while still selecting the wrong authority, citing a broad document instead of the supporting paragraph, treating an older disciplinary provision as current law, or blending theological commentary with an act of the Magisterium. This corpus supplies source-bound evidence and metadata so an answer system can retrieve the right text, preserve its authority and historical context, and cite only material actually present in the evidence packet.

Retrieval is an aid to theological reasoning, not a substitute for it. Applications should let the answer model synthesize naturally, use external official sources for current developments, and abstain when the installed corpus is insufficient.

## Quick start

Validate the complete repository using only the Python standard library:

```bash
python scripts/validate_repository.py
```

Read the first records:

```bash
python examples/python_load.py --limit 3
```

Each line in `data/retrieval_chunks.en.jsonl` and `data/retrieval_chunks.la.jsonl` is an independent JSON object. Embed `embedding_text`; retain the remaining fields for citation, filtering, and source recovery.

```python
import json

with open("data/retrieval_chunks.en.jsonl", encoding="utf-8") as stream:
    for line in stream:
        record = json.loads(line)
        vector_text = record["embedding_text"]
        citation = record["canonical_citation"]
        source_id = record["canonical_record_id"]
```

To generate the D1/SQLite import omitted from Git because it is a reproducible 84 MB build artifact:

```bash
python scripts/build_d1_import.py --package . --output build/d1_import.sql
```

## Recommended retrieval design

1. Resolve an explicitly named document, paragraph, canon, session, question, or quotation through `data/exact_locus_index.jsonl` before semantic search.
2. Fuse exact-locus, lexical/FTS, and dense-vector candidates.
3. Default to English; retrieve Latin only for Latin queries or explicit requests so bilingual parallels do not crowd out English evidence.
4. Use the CCC first for ordinary catechesis, then add the direct council, papal, or dicastery locus when the question asks for it.
5. Keep authority class, document type, issuing authority, date, language, and source URL attached to every result.
6. Expand only to source-defined parents or adjacent units when needed for context.
7. Build the answer model's citation allowlist only from passages actually included in its final evidence packet.
8. Retain verified official web retrieval for current law, discipline, documents issued after the acquisition date, or sources absent from this release.
9. Keep separate theological corpora—such as the *Summa Theologiae*—distinct and combine them only for genuinely mixed questions.

See [the retrieval guide](docs/RETRIEVAL_GUIDE.md) and [data schema](docs/DATA_SCHEMA.md) for implementation details.

## Repository layout

```text
source/canonical/      Source-faithful records grouped by document family
source/provenance/     Source catalog, edition data, limitations, and ledgers
source/derived/        Concept, cross-reference, authority, and neighbor indexes
source/validation/     Per-document validation and self-check evidence
data/                  Aggregated canonical rows and retrieval-ready chunks
metadata/              Ingestion and release metadata
audit/                 Independent audit and ingestion-validation evidence
schema/                D1/SQLite schema
scripts/               Deterministic builders and validators
tests/                 Retrieval acceptance cases
docs/                  Schema, retrieval, validation, and rights guidance
examples/              Minimal loading example
```

## Validation status

The canonical corpus and normalized retrieval layer passed the final independent audit:

| Gate | Result |
|---|---:|
| Canonical documents | 108 |
| Canonical records | 13,725 |
| Retrieval chunks | 13,828 |
| Exact-locus aliases | 23,825 |
| Five-percent fidelity sample | 687 records |
| Source-fidelity failures | 0 |
| Documented limitations in sample | 16 |
| Canonical errors after repair | 0 |
| Lossless chunk reconstruction failures | 0 |
| D1/SQLite `quick_check` | `ok` |

Seventy-three oversized source units were divided at paragraph or sentence boundaries into deterministic chunks. Concatenating those chunks reconstructs the canonical source text byte for byte.

The 16 documented limitations are preserved rather than silently “repaired.” See `source/provenance/limitations_ledger.json` and [the full audit](reports/FULL_AUDIT_REPORT.md).

## Text, sources, and rights

Source URLs, editions, translations, acquisition dates, limitations, and hashes are recorded in `source/provenance/source_catalog.json` and `source/provenance/source_editions.json`.

The repository's original code and documentation are available under the MIT License. To the extent AD IPSUM owns rights in the original corpus organization, metadata, schemas, and derived retrieval artifacts, those data-layer rights are dedicated under CC0 1.0. The underlying ecclesiastical texts and third-party translations retain their respective rights and are not relicensed by this repository.

Read [COPYRIGHT_AND_SOURCES.md](COPYRIGHT_AND_SOURCES.md) and [LICENSE-DATA.md](LICENSE-DATA.md) before redistribution.

## Citation

Use [CITATION.cff](CITATION.cff), or cite:

> AD IPSUM. *Catholic Doctrine and Magisterium Canonical RAG Corpus*, version 1.0.0, 2026.

When quoting a Church document, also cite its canonical locus and original source.

## Contributions

Corrections are welcome when supported by an official source, a documented authorized edition, or other verifiable textual witness. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Important scope note

This is a retrieval corpus, not an official critical edition, a theological-note adjudication engine, or a substitute for the Church's current official publications. Document-level authority classes aid retrieval; they do not determine the theological note of every proposition within a document.
