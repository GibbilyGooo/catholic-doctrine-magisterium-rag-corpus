#!/usr/bin/env python3
"""Dependency-free integrity validation for the public corpus repository."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL: {path}:{number}: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []

    manifest = json.loads((root / "metadata/INGESTION_MANIFEST.json").read_text(encoding="utf-8"))
    source_rows = []
    for path in sorted((root / "source/canonical").rglob("*.jsonl")):
        source_rows.extend(jsonl(path))
    canonical = list(jsonl(root / "data/canonical_records.en.jsonl"))
    canonical += list(jsonl(root / "data/canonical_records.la.jsonl"))
    chunks = list(jsonl(root / "data/retrieval_chunks.en.jsonl"))
    chunks += list(jsonl(root / "data/retrieval_chunks.la.jsonl"))
    loci = list(jsonl(root / "data/exact_locus_index.jsonl"))

    source_by_id = {row["record_id"]: row for row in source_rows}
    canonical_by_id = {row["record_id"]: row for row in canonical}
    chunk_by_id = {row["id"]: row for row in chunks}
    if len(source_by_id) != len(source_rows):
        errors.append("duplicate source canonical record IDs")
    if len(canonical_by_id) != len(canonical):
        errors.append("duplicate aggregated canonical record IDs")
    if len(chunk_by_id) != len(chunks):
        errors.append("duplicate retrieval chunk IDs")
    if set(source_by_id) != set(canonical_by_id):
        errors.append("source and aggregated canonical ID sets differ")

    for record_id, source in source_by_id.items():
        if digest(source["text"]) != source["source_text_sha256"]:
            errors.append(f"source text hash mismatch: {record_id}")
        aggregate = canonical_by_id.get(record_id)
        if aggregate and (aggregate["text"] != source["text"] or aggregate["source_text_sha256"] != source["source_text_sha256"]):
            errors.append(f"aggregated canonical text differs: {record_id}")

    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    for chunk in chunks:
        chunk_id = chunk["id"]
        grouped[chunk["canonical_record_id"]].append(chunk)
        if chunk["canonical_record_id"] not in canonical_by_id:
            errors.append(f"orphan chunk: {chunk_id}")
        if len(chunk_id.encode("utf-8")) > 64:
            errors.append(f"vector ID exceeds contract: {chunk_id}")
        if len(chunk["chunk_text"].split()) > 900:
            errors.append(f"chunk exceeds 900 words: {chunk_id}")
        if digest(chunk["chunk_text"]) != chunk["chunk_text_sha256"]:
            errors.append(f"chunk hash mismatch: {chunk_id}")
        if digest(chunk["embedding_text"]) != chunk["embedding_text_sha256"]:
            errors.append(f"embedding text hash mismatch: {chunk_id}")
        metadata_bytes = len(json.dumps(chunk["vectorize_metadata"], ensure_ascii=False).encode("utf-8"))
        if metadata_bytes > 10_240:
            errors.append(f"vector metadata exceeds contract: {chunk_id}")

    for record_id, record in canonical_by_id.items():
        ordered = sorted(grouped[record_id], key=lambda row: row["chunk_index"])
        if "".join(row["chunk_text"] for row in ordered) != record["text"]:
            errors.append(f"lossless reconstruction failed: {record_id}")
        if [row["id"] for row in ordered] != record["chunk_ids"]:
            errors.append(f"canonical chunk map differs: {record_id}")

    for locus in loci:
        if locus["record_id"] not in canonical_by_id:
            errors.append(f"orphan exact locus: {locus['record_id']}")
        for chunk_id in locus["chunk_ids"]:
            if chunk_id not in chunk_by_id:
                errors.append(f"orphan exact-locus chunk: {chunk_id}")

    catalog = json.loads((root / "data/document_catalog.json").read_text(encoding="utf-8"))
    provenance = json.loads((root / "source/provenance/source_catalog.json").read_text(encoding="utf-8"))
    observed = {
        "source_records": len(source_rows),
        "canonical_records": len(canonical),
        "retrieval_chunks": len(chunks),
        "exact_locus_aliases": len(loci),
        "catalog_documents": len(catalog),
        "provenance_documents": len(provenance["documents"]),
    }
    expected = {
        "canonical_records": manifest["canonical_records"],
        "retrieval_chunks": manifest["retrieval_chunks"],
        "exact_locus_aliases": manifest["exact_locus_aliases"],
        "documents": manifest["documents"],
    }
    if observed["source_records"] != expected["canonical_records"]:
        errors.append("source canonical count differs from manifest")
    if observed["canonical_records"] != expected["canonical_records"]:
        errors.append("aggregated canonical count differs from manifest")
    if observed["retrieval_chunks"] != expected["retrieval_chunks"]:
        errors.append("retrieval chunk count differs from manifest")
    if observed["exact_locus_aliases"] != expected["exact_locus_aliases"]:
        errors.append("exact-locus count differs from manifest")
    if observed["catalog_documents"] != expected["documents"] or observed["provenance_documents"] != expected["documents"]:
        errors.append("document count differs from manifest")

    report = {
        "status": "PASSED" if not errors else "FAILED",
        **observed,
        "max_chunk_words": max(len(row["chunk_text"].split()) for row in chunks),
        "max_vector_id_bytes": max(len(row["id"].encode("utf-8")) for row in chunks),
        "max_metadata_bytes": max(len(json.dumps(row["vectorize_metadata"], ensure_ascii=False).encode("utf-8")) for row in chunks),
        "error_count": len(errors),
        "errors": errors[:100],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
