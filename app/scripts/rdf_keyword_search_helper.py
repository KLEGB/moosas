"""
Robust RDF keyword search helper.

Designed for Code Interpreter usage:
- Parse RDF with rdflib across common formats when possible.
- Fall back to resilient text search if graph parsing fails.
- Provide a simple keyword query API for fast lookup.

Example (Python):
    from rdf_keyword_search_helper import keyword_query
    result = keyword_query("temp.rdf", "zone_c_temp", top_k=20)
    print(result["summary"])

Example (CLI):
    python rdf_keyword_search_helper.py --file temp.rdf --query zone_c_temp --top-k 20
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from rdflib import Graph
except Exception:  # rdflib may be unavailable in some runtime environments
    Graph = None  # type: ignore


COMMON_RDF_FORMATS = ["xml", "turtle", "n3", "nt", "json-ld", "trig"]


def _norm_text(value: Any) -> str:
    return str(value).strip()


def _tokenize(query: str) -> List[str]:
    return [t for t in re.split(r"\s+", query.lower().strip()) if t]


def _safe_read(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_text(errors="ignore")


def _graph_records(file_path: Path) -> Tuple[List[Dict[str, str]], str]:
    if Graph is None:
        return [], "rdflib-not-available"

    graph = Graph()
    used_format = ""
    parsed = False

    for rdf_format in COMMON_RDF_FORMATS:
        try:
            graph.parse(str(file_path), format=rdf_format)
            used_format = rdf_format
            parsed = True
            break
        except Exception:
            continue

    if not parsed:
        return [], "parse-failed"

    records: List[Dict[str, str]] = []
    for s, p, o in graph:
        records.append(
            {
                "subject": _norm_text(s),
                "predicate": _norm_text(p),
                "object": _norm_text(o),
            }
        )

    return records, f"parsed:{used_format}"


def _text_records(file_path: Path) -> List[Dict[str, str]]:
    raw = _safe_read(file_path)
    lines = raw.splitlines()

    # Keep this simple and robust: each non-empty line is searchable content.
    records: List[Dict[str, str]] = []
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        records.append(
            {
                "subject": f"line:{i}",
                "predicate": "raw_text",
                "object": line,
            }
        )
    return records


def _score_record(record: Dict[str, str], query: str, tokens: List[str]) -> int:
    hay = f"{record['subject']} {record['predicate']} {record['object']}".lower()
    score = 0

    if query.lower() in hay:
        score += 10

    for tok in tokens:
        if tok in hay:
            score += 3

    # Prefer hits in predicate/object as they are usually more useful.
    if query.lower() in record["predicate"].lower():
        score += 4
    if query.lower() in record["object"].lower():
        score += 4

    return score


def keyword_query(file_path: str, query: str, top_k: int = 20) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    records, parse_status = _graph_records(path)
    source = "graph"

    if not records:
        records = _text_records(path)
        source = "text-fallback"

    tokens = _tokenize(query)
    scored: List[Tuple[int, Dict[str, str]]] = []
    for rec in records:
        score = _score_record(rec, query, tokens)
        if score > 0:
            scored.append((score, rec))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: max(1, top_k)]

    matches = [
        {
            "score": score,
            "subject": rec["subject"],
            "predicate": rec["predicate"],
            "object": rec["object"],
        }
        for score, rec in top
    ]

    summary = {
        "file": str(path),
        "query": query,
        "parse_status": parse_status,
        "search_source": source,
        "total_records": len(records),
        "matched_records": len(scored),
        "returned": len(matches),
    }

    return {"summary": summary, "matches": matches}


def _main() -> None:
    parser = argparse.ArgumentParser(description="Keyword query helper for RDF files")
    parser.add_argument("--file", required=True, help="Path to RDF file")
    parser.add_argument("--query", required=True, help="Keyword query")
    parser.add_argument("--top-k", type=int, default=20, help="Max result count")
    parser.add_argument("--json-out", default="", help="Optional output JSON file path")
    args = parser.parse_args()

    result = keyword_query(args.file, args.query, top_k=args.top_k)

    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    for i, row in enumerate(result["matches"], start=1):
        print(f"[{i}] score={row['score']}")
        print(f"  s: {row['subject']}")
        print(f"  p: {row['predicate']}")
        print(f"  o: {row['object']}")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved full result to: {out_path}")


if __name__ == "__main__":
    _main()
