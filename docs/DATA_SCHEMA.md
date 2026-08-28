# Data schema

## Canonical records

The source-faithful per-document JSONL files live under `source/canonical/`. Each record includes:

- `record_id`: stable corpus identifier;
- `canonical_citation`: natural scholarly display citation;
- `document_abbrev`, `document_title`, and `document_type`;
- `source_family` and `authority_class`;
- structured loci such as paragraph, canon, session, question, chapter, or section when applicable;
- promulgating authority and date;
- language and bilingual `parallel_group_id`;
- source name, URL, locator, edition, and translator when known;
- exact `text`, attached `footnotes`, and `source_text_sha256`.

Fields that do not apply to a document family are null rather than fabricated.

## Aggregated canonical rows

`data/canonical_records.en.jsonl` and `data/canonical_records.la.jsonl` normalize the canonical records for database ingestion and attach record-neighbor and chunk mappings. The exact text and source hash remain unchanged.

## Retrieval chunks

`data/retrieval_chunks.en.jsonl` and `data/retrieval_chunks.la.jsonl` include:

- deterministic `id`;
- `canonical_record_id` and canonical citation;
- authority, family, document, language, and date filters;
- zero-based `chunk_index` and total `chunk_count`;
- exact `chunk_text` and its hash;
- enriched `embedding_text` and its hash;
- previous and next chunk links;
- compact `vectorize_metadata`.

Only 73 canonical records required subdivision. Joining their `chunk_text` values in `chunk_index` order reconstructs the canonical text exactly. No overlapping text is introduced.

## Exact-locus index

Each row in `data/exact_locus_index.jsonl` maps a normalized citation alias and language to a canonical record and its retrieval chunks. Use this before semantic search whenever the user names a document or locus.

## Document catalog

`data/document_catalog.json` provides document-level routing metadata and installed-language counts. It is a routing aid, not a proposition-level authority judgment.
