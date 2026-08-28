#!/usr/bin/env python3
"""Convert prepared JSONL into D1-compatible single-row SQL statements."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip(): yield json.loads(line)

def sql(value):
    if value is None: return "NULL"
    if isinstance(value, (int, float)): return str(value)
    return "'" + str(value).replace("'", "''") + "'"

def main():
    p=argparse.ArgumentParser(); p.add_argument("--package",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); root=a.package.resolve()
    canon=list(rows(root/"data/canonical_records.en.jsonl"))+list(rows(root/"data/canonical_records.la.jsonl"))
    chunks=list(rows(root/"data/retrieval_chunks.en.jsonl"))+list(rows(root/"data/retrieval_chunks.la.jsonl"))
    loci=list(rows(root/"data/exact_locus_index.jsonl"))
    columns_record=("record_id","canonical_citation","document_abbrev","document_title","document_type","source_family","source_family_canonical","authority_class","language","date_promulgated","parallel_group_id","source_name","source_url","source_locator","text","footnotes_json","source_text_sha256","previous_record_id","next_record_id","chunk_ids_json")
    columns_chunk=("id","canonical_record_id","canonical_citation","document_abbrev","document_title","document_type","source_family","source_family_canonical","authority_class","language","date_promulgated","chunk_index","chunk_count","chunk_text","chunk_text_sha256","source_text_sha256","embedding_text","embedding_text_sha256","previous_chunk_id","next_chunk_id")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",encoding="utf-8",newline="\n") as out:
        out.write((root/"schema/d1_schema.sql").read_text(encoding="utf-8"))
        out.write("CREATE VIRTUAL TABLE retrieval_chunks_fts USING fts5(id UNINDEXED, embedding_text, canonical_citation, document_title, tokenize='unicode61 remove_diacritics 2');\n")
        for r in canon:
            shaped=dict(r); shaped["footnotes_json"]=json.dumps(r["footnotes"],ensure_ascii=False,separators=(",",":")); shaped["chunk_ids_json"]=json.dumps(r["chunk_ids"],separators=(",",":"))
            out.write(f"INSERT INTO canonical_records ({','.join(columns_record)}) VALUES ({','.join(sql(shaped.get(c)) for c in columns_record)});\n")
        for r in chunks:
            out.write(f"INSERT INTO retrieval_chunks ({','.join(columns_chunk)}) VALUES ({','.join(sql(r.get(c)) for c in columns_chunk)});\n")
            out.write("INSERT INTO retrieval_chunks_fts (id,embedding_text,canonical_citation,document_title) VALUES ("+",".join(sql(r.get(c)) for c in ("id","embedding_text","canonical_citation","document_title"))+");\n")
        for r in loci:
            values=(r["normalized_key"],r["language"],r["record_id"],r["canonical_citation"],json.dumps(r["chunk_ids"],separators=(",",":")))
            out.write("INSERT INTO exact_locus (normalized_key,language,record_id,canonical_citation,chunk_ids_json) VALUES ("+",".join(sql(v) for v in values)+");\n")
    print(json.dumps({"canonical_records":len(canon),"retrieval_chunks":len(chunks),"fts_rows":len(chunks),"exact_locus_rows":len(loci),"output":str(a.output),"bytes":a.output.stat().st_size},indent=2))
if __name__=="__main__": main()
