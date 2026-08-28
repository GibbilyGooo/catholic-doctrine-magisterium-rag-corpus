# Retrieval guide

## Query path

1. Detect explicit document names, abbreviations, paragraphs, canons, sessions, questions, or requested quotations.
2. Resolve them through the exact-locus index.
3. Run lexical/FTS and dense search when the request is topical rather than locus-specific.
4. Fuse and rerank a bounded candidate set.
5. Expand to source-defined parents or immediate neighbors only when the answer needs context.
6. Build an evidence packet within the model's token budget.
7. Allow citations only to passages actually included in that final packet.

## Authority-aware selection

- Use the CCC first for ordinary catechesis.
- Use the Compendium as a concise entry point and follow its normalized CCC references.
- Retrieve direct conciliar definitions or canons for council questions.
- Retrieve the named papal or dicastery document for document-specific moral, social, bioethical, or doctrinal questions.
- Never convert a document-level authority class into a universal `infallible` boolean.
- Keep Magisterium and theological-author corpora distinct in mixed questions.

## Language

Default to English. Latin parallels should surface only for a Latin query, an explicit request, or a deliberate parallel-text feature. Otherwise bilingual near-duplicates can consume the candidate set.

## Current-source fallback

Use a verified official external source when the request concerns current canon law, present discipline, a later revision, a document after the corpus acquisition date, or a source absent from this release. The local corpus should never disable external tools.

## Cloudflare reference architecture

The prepared records fit a hybrid architecture using D1/SQLite for canonical text, exact loci, and FTS, plus a separate dense-vector index over `embedding_text`. `schema/d1_schema.sql` and `scripts/build_d1_import.py` are supplied as one implementation path. Other databases and embedding systems can use the same vendor-neutral JSONL.

Do not mix these vectors into an unrelated corpus index. Separate indexes make authority, language, lifecycle, and fallback behavior easier to control.
