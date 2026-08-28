-- Vendor-neutral D1 schema; no credentials, bindings, or deployment actions.
PRAGMA foreign_keys = ON;
CREATE TABLE canonical_records (
  record_id TEXT PRIMARY KEY, canonical_citation TEXT NOT NULL, document_abbrev TEXT NOT NULL,
  document_title TEXT NOT NULL, document_type TEXT, source_family TEXT NOT NULL, source_family_canonical TEXT NOT NULL,
  authority_class TEXT NOT NULL, language TEXT NOT NULL, date_promulgated TEXT, parallel_group_id TEXT NOT NULL,
  source_name TEXT, source_url TEXT NOT NULL, source_locator TEXT, text TEXT NOT NULL, footnotes_json TEXT NOT NULL,
  source_text_sha256 TEXT NOT NULL, previous_record_id TEXT, next_record_id TEXT, chunk_ids_json TEXT NOT NULL
);
CREATE TABLE retrieval_chunks (
  id TEXT PRIMARY KEY, canonical_record_id TEXT NOT NULL REFERENCES canonical_records(record_id),
  canonical_citation TEXT NOT NULL, document_abbrev TEXT NOT NULL, document_title TEXT NOT NULL,
  document_type TEXT, source_family TEXT NOT NULL, source_family_canonical TEXT NOT NULL, authority_class TEXT NOT NULL,
  language TEXT NOT NULL, date_promulgated TEXT, chunk_index INTEGER NOT NULL, chunk_count INTEGER NOT NULL,
  chunk_text TEXT NOT NULL, chunk_text_sha256 TEXT NOT NULL, source_text_sha256 TEXT NOT NULL,
  embedding_text TEXT NOT NULL, embedding_text_sha256 TEXT NOT NULL, previous_chunk_id TEXT, next_chunk_id TEXT
);
CREATE TABLE exact_locus (
  normalized_key TEXT NOT NULL, language TEXT NOT NULL, record_id TEXT NOT NULL REFERENCES canonical_records(record_id),
  canonical_citation TEXT NOT NULL, chunk_ids_json TEXT NOT NULL, PRIMARY KEY(normalized_key, language, record_id)
);
CREATE INDEX idx_records_citation ON canonical_records(canonical_citation, language);
CREATE INDEX idx_records_document ON canonical_records(document_abbrev, language);
CREATE INDEX idx_records_family ON canonical_records(source_family, authority_class, language);
CREATE INDEX idx_chunks_record ON retrieval_chunks(canonical_record_id, chunk_index);
CREATE INDEX idx_chunks_filter ON retrieval_chunks(source_family, authority_class, language, document_abbrev);
CREATE INDEX idx_locus_key ON exact_locus(normalized_key, language);
