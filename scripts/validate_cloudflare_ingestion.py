#!/usr/bin/env python3
"""Validate the generated Cloudflare ingestion companion without dependencies."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

def digest(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()
def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip(): yield json.loads(line)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--package",type=Path,required=True); a=p.parse_args(); root=a.package.resolve()
    manifest=json.loads((root/"metadata/INGESTION_MANIFEST.json").read_text(encoding="utf-8"))
    canonical=list(rows(root/"data/canonical_records.en.jsonl"))+list(rows(root/"data/canonical_records.la.jsonl"))
    chunks=list(rows(root/"data/retrieval_chunks.en.jsonl"))+list(rows(root/"data/retrieval_chunks.la.jsonl"))
    loci=list(rows(root/"data/exact_locus_index.jsonl")); errors=[]
    records={r["record_id"]:r for r in canonical}; chunk_map={c["id"]:c for c in chunks}
    if len(records)!=len(canonical): errors.append("duplicate canonical record IDs")
    if len(chunk_map)!=len(chunks): errors.append("duplicate chunk IDs")
    for c in chunks:
        if len(c["id"].encode())>64: errors.append(f"vector id too long: {c['id']}")
        if len(json.dumps(c["vectorize_metadata"],ensure_ascii=False).encode())>10240: errors.append(f"metadata too large: {c['id']}")
        if len(c["chunk_text"].split())>900: errors.append(f"chunk too long: {c['id']}")
        if digest(c["chunk_text"])!=c["chunk_text_sha256"]: errors.append(f"chunk hash mismatch: {c['id']}")
        if digest(c["embedding_text"])!=c["embedding_text_sha256"]: errors.append(f"embedding hash mismatch: {c['id']}")
        if c["canonical_record_id"] not in records: errors.append(f"orphan chunk: {c['id']}")
    grouped=collections.defaultdict(list)
    for c in chunks: grouped[c["canonical_record_id"]].append(c)
    for rid, record in records.items():
        ordered=sorted(grouped[rid],key=lambda x:x["chunk_index"])
        if "".join(c["chunk_text"] for c in ordered)!=record["text"]: errors.append(f"lossless reconstruction failed: {rid}")
        if [c["id"] for c in ordered]!=record["chunk_ids"]: errors.append(f"chunk map mismatch: {rid}")
        if digest(record["text"])!=record["source_text_sha256"]: errors.append(f"source hash mismatch: {rid}")
    for row in loci:
        if row["record_id"] not in records: errors.append(f"orphan locus: {row['record_id']}")
        if any(cid not in chunk_map for cid in row["chunk_ids"]): errors.append(f"orphan locus chunk: {row['record_id']}")
    expected=(manifest["canonical_records"],manifest["retrieval_chunks"],manifest["exact_locus_aliases"])
    observed=(len(canonical),len(chunks),len(loci))
    if expected!=observed: errors.append(f"manifest counts differ: {expected} != {observed}")
    report={"schema_version":"theology_ai_magisterium_ingestion_validation_v1","status":"PASSED" if not errors else "FAILED","canonical_records":len(canonical),"retrieval_chunks":len(chunks),"exact_locus_aliases":len(loci),"max_chunk_words":max(len(c['chunk_text'].split()) for c in chunks),"max_vector_id_bytes":max(len(c['id'].encode()) for c in chunks),"max_metadata_bytes":max(len(json.dumps(c['vectorize_metadata'],ensure_ascii=False).encode()) for c in chunks),"error_count":len(errors),"errors":errors[:100]}
    (root/"audit/INGESTION_VALIDATION.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if errors: raise SystemExit(1)
if __name__=="__main__": main()
