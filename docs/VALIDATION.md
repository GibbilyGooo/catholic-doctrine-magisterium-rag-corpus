# Validation

Run:

```bash
python scripts/validate_repository.py
```

The validator checks:

- source and aggregated canonical record counts;
- stable unique record and chunk IDs;
- source-text and chunk hashes;
- exact equality between canonical and aggregated source text;
- lossless chunk reconstruction;
- exact-locus foreign keys;
- document-catalog and provenance counts;
- chunk, vector-ID, and metadata size limits recorded by the release contract.

The frozen audit evidence is under `audit/`, `source/validation/`, and `reports/`. The five-percent fidelity review evaluated 687 records spanning all 108 documents. It recorded zero source-fidelity failures and 16 explicitly documented limitations.

Validation demonstrates corpus integrity and retrieval readiness. It does not claim that every historical edition is a critical edition or that the corpus includes every Church document that may be relevant to a future question.
