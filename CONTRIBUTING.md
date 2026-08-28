# Contributing

Corrections and retrieval improvements are welcome when they preserve source fidelity and Catholic authority distinctions.

## Text corrections

Open an issue or pull request that includes:

- the affected `record_id` and canonical citation;
- the proposed exact replacement;
- an official source URL, authorized edition, scan, or other verifiable witness;
- an explanation of whether the change affects text, metadata, a source locator, or a documented limitation.

Do not normalize historical wording, modernize a translation, remove apparent duplication, or repair a source irregularity without evidence. Known limitations are intentionally retained in `source/provenance/limitations_ledger.json`.

## Retrieval changes

Changes to chunking, aliases, authority metadata, or routing guidance should preserve:

- canonical source text byte for byte;
- stable canonical record IDs;
- exact-locus precedence;
- language separation;
- authority-class distinctions;
- lossless chunk reconstruction;
- external-source fallback for current or missing authority.

Run `python scripts/validate_repository.py` before submitting a pull request.
