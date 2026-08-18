"""Knowledge ingestion: read knowledge_chunks.jsonl -> embed -> ChromaDB.

Usage:
    python -m src.ingest --data mock_kb/knowledge_chunks.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Default paths are relative to the `four/` directory.
DEFAULT_DB_PATH = "fin_sight_db"
COLLECTION_NAME = "fish_disease_kb"
REMOTE_MODEL_NAME = "all-MiniLM-L6-v2"
LOCAL_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "all-MiniLM-L6-v2")


def resolve_model_name() -> str:
    """Pick the embedding model: env override -> local copy -> HuggingFace id."""
    env = os.environ.get("FINSIGHT_MODEL_PATH")
    if env:
        return env
    local = os.path.abspath(LOCAL_MODEL_DIR)
    if os.path.isdir(local) and os.path.exists(os.path.join(local, "config.json")):
        return local
    return REMOTE_MODEL_NAME

# Metadata fields copied into the vector DB so the retriever can filter.
META_FIELDS = [
    "chunk_id",
    "condition_id",
    "condition_name",
    "evidence_type",
    "source_id",
    "source_title",
    "section",
    "source_url",
]


def load_chunks(path: str) -> list[dict]:
    """Load a JSONL knowledge file into a list of chunk dicts."""
    chunks: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[warn] skip malformed line {line_no}: {e}")
                continue
            if "text" not in chunk:
                print(f"[warn] skip line {line_no}: missing 'text'")
                continue
            chunks.append(chunk)
    return chunks


def build_collection(db_path: str) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=db_path)
    model_name = resolve_model_name()
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=ef
    )
    return collection


def ingest(data_file: str, db_path: str = DEFAULT_DB_PATH) -> int:
    chunks = load_chunks(data_file)
    if not chunks:
        print("[warn] no chunks loaded, nothing to ingest")
        return 0

    collection = build_collection(db_path)

    docs: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    for chunk in chunks:
        docs.append(chunk["text"])
        metadata = {k: chunk.get(k, "") for k in META_FIELDS}
        metadatas.append(metadata)
        ids.append(chunk.get("chunk_id", f"chunk_{len(ids)}"))

    collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
    print(f"[ok] ingested {len(docs)} chunks into collection '{COLLECTION_NAME}'")
    print(f"[ok] db path: {os.path.abspath(db_path)}")
    return len(docs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge chunks into ChromaDB")
    parser.add_argument("--data", default="mock_kb/knowledge_chunks.jsonl")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    data = Path(args.data)
    if not data.exists():
        print(f"[error] data file not found: {data}")
        raise SystemExit(1)

    ingest(str(data), args.db)


if __name__ == "__main__":
    main()
