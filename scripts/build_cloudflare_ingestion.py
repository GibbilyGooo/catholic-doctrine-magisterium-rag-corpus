#!/usr/bin/env python3
"""Build a deterministic, no-credentials Cloudflare ingestion companion."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import shutil
from pathlib import Path

TARGET_WORDS = 650
SOFT_MAX_WORDS = 800
HARD_MAX_WORDS = 900


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_text(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def json_line(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def normalize_key(value: str) -> str:
    value = value.casefold().replace("§", " ")
    value = re.sub(r"[\[\](){},.;:]", " ", value)
    value = re.sub(r"\b(?:paragraph|para|number|no)\.?\s+", "", value)
    return " ".join(value.split())


def split_exact(text: str) -> list[str]:
    """Split on preferred source boundaries while preserving every character."""
    words = list(re.finditer(r"\S+", text))
    if len(words) <= HARD_MAX_WORDS:
        return [text]
    pieces: list[str] = []
    start_char = 0
    start_word = 0
    total = len(words)
    while total - start_word > HARD_MAX_WORDS:
        target = min(start_word + TARGET_WORDS, total)
        soft = min(start_word + SOFT_MAX_WORDS, total)
        minimum = min(start_word + 450, target)
        chosen = None
        # Prefer a paragraph or sentence ending nearest the target, without
        # crossing the soft limit.  Canonical source order is never changed.
        for index in range(soft - 1, minimum - 2, -1):
            word = words[index].group(0)
            gap_end = words[index + 1].start() if index + 1 < total else len(text)
            gap = text[words[index].end():gap_end]
            if "\n\n" in gap or re.search(r"[.!?…][\]\)\"'’”]*$", word):
                chosen = index + 1
                if chosen <= target + 40:
                    break
        if chosen is None:
            chosen = target
        cut_char = words[chosen - 1].end()
        pieces.append(text[start_char:cut_char])
        start_char = cut_char
        start_word = chosen
    pieces.append(text[start_char:])
    if "".join(pieces) != text:
        raise AssertionError("lossless split invariant failed")
    if any(len(piece.split()) > HARD_MAX_WORDS for piece in pieces):
        raise AssertionError("hard word limit exceeded")
    return pieces


def retrieval_family(value: str) -> str:
    return "dicastery" if value == "doctrinal_dicastery" else value


def aliases(record: dict) -> list[str]:
    citation = record["canonical_citation"]
    abbrev = record["document_abbrev"]
    values = {citation, f"{abbrev} {citation.removeprefix(abbrev).strip()}"}
    if abbrev == "CCC" and record.get("paragraph") is not None:
        values |= {f"Catechism {record['paragraph']}", f"CCC paragraph {record['paragraph']}"}
    if abbrev == "CCCC" and record.get("question") is not None:
        values |= {f"Compendium {record['question']}", f"CCCC question {record['question']}"}
    return sorted({normalize_key(v) for v in values if normalize_key(v)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_release.resolve()
    # In the public repository, --source-release points directly to source/.
    # The historical frozen release used an additional wrapper directory.
    corpus = source
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    for directory in ("data", "schema", "tests", "scripts", "audit"):
        (output / directory).mkdir(parents=True, exist_ok=True)

    parent_data = json.loads((corpus / "derived/parent_neighbor_expansion.json").read_text(encoding="utf-8"))
    parent_map = {item["record_id"]: item for item in parent_data["records"]}
    records = []
    for path in sorted((corpus / "canonical").rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    records.sort(key=lambda r: r["record_id"])

    chunks = []
    canonical_rows = []
    locus_rows = []
    documents = {}
    source_to_chunks = {}
    for record in records:
        rid = record["record_id"]
        parts = split_exact(record["text"])
        chunk_ids = []
        for index, body in enumerate(parts):
            stable = digest_text(f"magisterium-v1\0{rid}\0{index}")[:40]
            chunk_id = f"m2-{stable}"
            chunk_ids.append(chunk_id)
            header = [
                f"Document: {record['document_title']} ({record['document_abbrev']})",
                f"Citation: {record['canonical_citation']}",
                f"Authority: {record['authority_class']}",
                f"Date: {record['date_promulgated']}",
                f"Language: {record['language']}",
            ]
            if record.get("unit_title"):
                header.append(f"Unit: {record['unit_title']}")
            embedding_text = "\n".join(header) + "\n\n" + body.strip()
            metadata = {
                "rid": rid,
                "doc": record["document_abbrev"],
                "family": retrieval_family(record["source_family"]),
                "authority": record["authority_class"],
                "lang": record["language"],
                "date": record["date_promulgated"],
                "citation": record["canonical_citation"],
                "chunk": index,
                "chunks": len(parts),
            }
            chunks.append({
                "id": chunk_id,
                "canonical_record_id": rid,
                "canonical_citation": record["canonical_citation"],
                "document_abbrev": record["document_abbrev"],
                "document_title": record["document_title"],
                "document_type": record["document_type"],
                "source_family": retrieval_family(record["source_family"]),
                "source_family_canonical": record["source_family"],
                "authority_class": record["authority_class"],
                "language": record["language"],
                "date_promulgated": record["date_promulgated"],
                "chunk_index": index,
                "chunk_count": len(parts),
                "chunk_text": body,
                "chunk_text_sha256": digest_text(body),
                "source_text_sha256": record["source_text_sha256"],
                "embedding_text": embedding_text,
                "embedding_text_sha256": digest_text(embedding_text),
                "vectorize_metadata": metadata,
            })
        source_to_chunks[rid] = chunk_ids
        navigation = parent_map[rid]
        canonical_rows.append({
            "record_id": rid,
            "canonical_citation": record["canonical_citation"],
            "document_abbrev": record["document_abbrev"],
            "document_title": record["document_title"],
            "document_type": record["document_type"],
            "source_family": retrieval_family(record["source_family"]),
            "source_family_canonical": record["source_family"],
            "authority_class": record["authority_class"],
            "language": record["language"],
            "date_promulgated": record["date_promulgated"],
            "parallel_group_id": record["parallel_group_id"],
            "source_name": record["source_name"],
            "source_url": record["source_url"],
            "source_locator": record["source_locator"],
            "text": record["text"],
            "footnotes": record["footnotes"],
            "source_text_sha256": record["source_text_sha256"],
            "previous_record_id": navigation.get("previous_record_id"),
            "next_record_id": navigation.get("next_record_id"),
            "chunk_ids": chunk_ids,
        })
        for key in aliases(record):
            locus_rows.append({"normalized_key": key, "language": record["language"], "record_id": rid, "canonical_citation": record["canonical_citation"], "chunk_ids": chunk_ids})
        documents.setdefault(record["document_abbrev"], {
            "document_abbrev": record["document_abbrev"],
            "document_title": record["document_title"],
            "source_family": retrieval_family(record["source_family"]),
            "authority_class": record["authority_class"],
            "document_type": record["document_type"],
            "promulgating_authority": record["promulgating_authority"],
            "date_promulgated": record["date_promulgated"],
            "languages": set(), "record_count": 0, "chunk_count": 0,
        })
        documents[record["document_abbrev"]]["languages"].add(record["language"])
        documents[record["document_abbrev"]]["record_count"] += 1
        documents[record["document_abbrev"]]["chunk_count"] += len(parts)

    # Add deterministic within-record and cross-record chunk navigation.
    by_id = {chunk["id"]: chunk for chunk in chunks}
    for rid, ids in source_to_chunks.items():
        nav = parent_map[rid]
        previous_ids = source_to_chunks.get(nav.get("previous_record_id"), [])
        next_ids = source_to_chunks.get(nav.get("next_record_id"), [])
        for index, chunk_id in enumerate(ids):
            chunk = by_id[chunk_id]
            chunk["previous_chunk_id"] = ids[index - 1] if index else (previous_ids[-1] if previous_ids else None)
            chunk["next_chunk_id"] = ids[index + 1] if index + 1 < len(ids) else (next_ids[0] if next_ids else None)

    for language in ("en", "la"):
        (output / f"data/retrieval_chunks.{language}.jsonl").write_text("".join(json_line(x) for x in chunks if x["language"] == language), encoding="utf-8")
        (output / f"data/canonical_records.{language}.jsonl").write_text("".join(json_line(x) for x in canonical_rows if x["language"] == language), encoding="utf-8")
    (output / "data/exact_locus_index.jsonl").write_text("".join(json_line(x) for x in sorted(locus_rows, key=lambda x: (x["normalized_key"], x["language"], x["record_id"]))), encoding="utf-8")
    document_rows = []
    for item in documents.values():
        item["languages"] = sorted(item["languages"])
        document_rows.append(item)
    (output / "data/document_catalog.json").write_text(json.dumps(sorted(document_rows, key=lambda x: x["document_abbrev"]), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    schema = """-- Vendor-neutral D1 schema; no credentials, bindings, or deployment actions.\nPRAGMA foreign_keys = ON;\nCREATE TABLE canonical_records (\n  record_id TEXT PRIMARY KEY, canonical_citation TEXT NOT NULL, document_abbrev TEXT NOT NULL,\n  document_title TEXT NOT NULL, document_type TEXT, source_family TEXT NOT NULL, source_family_canonical TEXT NOT NULL,\n  authority_class TEXT NOT NULL, language TEXT NOT NULL, date_promulgated TEXT, parallel_group_id TEXT NOT NULL,\n  source_name TEXT, source_url TEXT NOT NULL, source_locator TEXT, text TEXT NOT NULL, footnotes_json TEXT NOT NULL,\n  source_text_sha256 TEXT NOT NULL, previous_record_id TEXT, next_record_id TEXT, chunk_ids_json TEXT NOT NULL\n);\nCREATE TABLE retrieval_chunks (\n  id TEXT PRIMARY KEY, canonical_record_id TEXT NOT NULL REFERENCES canonical_records(record_id),\n  canonical_citation TEXT NOT NULL, document_abbrev TEXT NOT NULL, document_title TEXT NOT NULL,\n  document_type TEXT, source_family TEXT NOT NULL, source_family_canonical TEXT NOT NULL, authority_class TEXT NOT NULL,\n  language TEXT NOT NULL, date_promulgated TEXT, chunk_index INTEGER NOT NULL, chunk_count INTEGER NOT NULL,\n  chunk_text TEXT NOT NULL, chunk_text_sha256 TEXT NOT NULL, source_text_sha256 TEXT NOT NULL,\n  embedding_text TEXT NOT NULL, embedding_text_sha256 TEXT NOT NULL, previous_chunk_id TEXT, next_chunk_id TEXT\n);\nCREATE TABLE exact_locus (\n  normalized_key TEXT NOT NULL, language TEXT NOT NULL, record_id TEXT NOT NULL REFERENCES canonical_records(record_id),\n  canonical_citation TEXT NOT NULL, chunk_ids_json TEXT NOT NULL, PRIMARY KEY(normalized_key, language, record_id)\n);\nCREATE INDEX idx_records_citation ON canonical_records(canonical_citation, language);\nCREATE INDEX idx_records_document ON canonical_records(document_abbrev, language);\nCREATE INDEX idx_records_family ON canonical_records(source_family, authority_class, language);\nCREATE INDEX idx_chunks_record ON retrieval_chunks(canonical_record_id, chunk_index);\nCREATE INDEX idx_chunks_filter ON retrieval_chunks(source_family, authority_class, language, document_abbrev);\nCREATE INDEX idx_locus_key ON exact_locus(normalized_key, language);\n"""
    (output / "schema/d1_schema.sql").write_text(schema, encoding="utf-8")

    cases = [
        {"id":"ccc_460","query":"What does CCC 460 teach?","expected_loci":["CCC 460"],"route":"exact_locus"},
        {"id":"cccc_39","query":"Compendium question 39","expected_loci":["CCCC 39"],"route":"exact_locus_then_ccc_expansion"},
        {"id":"nicaea_homoousios","query":"What did Nicaea I define about the Son being consubstantial with the Father?","expected_documents":["NIC1"],"route":"council_precision"},
        {"id":"chalcedon_two_natures","query":"Explain Chalcedon's definition of Christ in two natures.","expected_documents":["CHAL"],"route":"council_precision"},
        {"id":"ephesus_theotokos","query":"What did Ephesus teach concerning Mary as Theotokos?","expected_documents":["EPH"],"route":"council_precision"},
        {"id":"constantinople_two_wills","query":"Which council defined Christ's two wills and operations?","expected_documents":["CON3"],"route":"council_precision"},
        {"id":"trent_justification","query":"What does Trent teach about justification and grace?","expected_documents":["Trent"],"route":"council_precision"},
        {"id":"vatican_i_infallibility","query":"What conditions does Pastor Aeternus give for papal infallibility?","expected_documents":["PA"],"route":"council_precision"},
        {"id":"dei_filius_reason","query":"How does Dei Filius relate faith and reason?","expected_documents":["DF"],"route":"council_precision"},
        {"id":"lg_church","query":"What does Lumen Gentium teach about the nature of the Church?","expected_documents":["LG"],"route":"document_precision"},
        {"id":"dv_revelation","query":"How does Dei Verbum describe Scripture and Tradition?","expected_documents":["DV"],"route":"document_precision"},
        {"id":"gs_dignity","query":"What does Gaudium et Spes teach about human dignity?","expected_documents":["GS"],"route":"document_precision"},
        {"id":"dh_freedom","query":"Explain Dignitatis Humanae on religious freedom.","expected_documents":["DH"],"route":"document_precision"},
        {"id":"hv_contraception","query":"What does Humanae Vitae teach about contraception?","expected_documents":["HV"],"route":"document_precision"},
        {"id":"vs_intrinsic_evil","query":"What does Veritatis Splendor teach about intrinsically evil acts?","expected_documents":["VS"],"route":"document_precision"},
        {"id":"ev_life","query":"What does Evangelium Vitae teach about abortion and euthanasia?","expected_documents":["EV"],"route":"document_precision"},
        {"id":"di_salvation","query":"What does Dominus Iesus teach about Christ and salvation?","expected_documents":["DI"],"route":"dicastery_precision"},
        {"id":"dp_embryo","query":"What does Dignitas Personae teach about human embryos?","expected_documents":["DP"],"route":"dicastery_precision"},
        {"id":"din_dignity","query":"How does Dignitas Infinita explain human dignity?","expected_documents":["DIN"],"route":"dicastery_precision"},
        {"id":"current_law_fallback","query":"What is the current canon-law procedure in force today?","expected_behavior":"external_current_authority_required","route":"external_fallback"},
        {"id":"summa_separation","query":"How does Aquinas argue for divine simplicity?","expected_behavior":"summa_corpus_not_magisterium_only","route":"summa_or_mixed"},
        {"id":"latin_filter","query":"Da mihi textum Latinum CCC 460.","expected_loci":["CCC 460 [Latin]"],"route":"exact_locus_latin"},
        {"id":"ordinary_catechesis","query":"Why do Catholics baptize infants?","expected_documents":["CCC"],"route":"ccc_first"},
        {"id":"authority_no_flattening","query":"Is every sentence in every dicastery document infallible?","expected_behavior":"no_simplistic_infallibility_flag","route":"authority_context"}
    ]
    (output / "tests/retrieval_acceptance_cases.json").write_text(json.dumps({"schema_version":"theology_ai_magisterium_retrieval_acceptance_v1","cases":cases}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    shutil.copy2(Path(__file__).resolve(), output / "scripts/build_cloudflare_ingestion.py")
    counts = collections.Counter(chunk["language"] for chunk in chunks)
    split_records = sum(len(ids) > 1 for ids in source_to_chunks.values())
    manifest = {
        "schema_version": "theology_ai_magisterium_cloudflare_ingestion_v1",
        "status": "INGESTION_READY_NO_DEPLOYMENT_PERFORMED",
        "source_release_sha256": digest_file(source / "RELEASE_MANIFEST.json"),
        "canonical_records": len(records),
        "retrieval_chunks": len(chunks),
        "retrieval_chunks_by_language": dict(sorted(counts.items())),
        "records_split": split_records,
        "documents": len(documents),
        "exact_locus_aliases": len(locus_rows),
        "chunking": {"method":"lossless source-boundary-aware","target_words":TARGET_WORDS,"soft_max_words":SOFT_MAX_WORDS,"hard_max_words":HARD_MAX_WORDS,"overlap_words":0,"neighbor_expansion":True},
        "vectorize": {"embedding_model":"@cf/baai/bge-m3","dimensions":1024,"metric":"cosine","vector_id_max_bytes":64,"generated_id_bytes":43,"metadata_max_bytes":10240,"language_default":"en","latin_policy":"retrieve only for Latin query or explicit request"},
        "normalizations": {"doctrinal_dicastery":"dicastery", "canonical_source_family_preserved_separately":True},
        "prohibitions": ["no credentials", "no Cloudflare resource creation", "no deployment", "no embeddings included", "do not merge with Summa index"],
    }
    (output / "INGESTION_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
