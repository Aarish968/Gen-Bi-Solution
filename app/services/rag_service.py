"""
rag_service.py

RAG (Retrieval-Augmented Generation) Service.

Embeddings: HuggingFace all-MiniLM-L6-v2 (local, no API key, no quota)
  - Runs entirely on local machine
  - 384-dimensional vectors
  - Downloaded once from HuggingFace Hub, cached locally after that

Why HuggingFace instead of Gemini embeddings:
  - Groq does not provide embedding models
  - HuggingFace local embeddings = zero API cost, zero quota limits
  - Fast — runs on CPU, no network call needed after first download

Supported file types: .txt, .pdf, .csv
Persistence: FAISS index + docs saved to disk after every upload
"""

import io
import os
import csv
import json
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Disk paths
FAISS_INDEX_PATH = "data/faiss_index.bin"
FAISS_DOCS_PATH  = "data/faiss_docs.json"

# all-MiniLM-L6-v2 outputs 384-dim vectors
EMBEDDING_DIM = 384


class RAGService:
    def __init__(self):
        # Downloaded once from HuggingFace Hub, cached in ~/.cache/huggingface/
        # Subsequent startups load from cache — no internet needed
        print("[RAGService] Loading HuggingFace embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("[RAGService] Embedding model loaded.")

        self.index, self.docs = self._load_from_disk()

    # ─────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────

    def _load_from_disk(self):
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_DOCS_PATH):
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_DOCS_PATH, "r", encoding="utf-8") as f:
                docs = json.load(f)
            print(f"[RAGService] Loaded {len(docs)} chunks from disk.")
            return index, docs

        print("[RAGService] No existing index found. Starting fresh.")
        return faiss.IndexFlatL2(EMBEDDING_DIM), []

    def _save_to_disk(self):
        os.makedirs("data", exist_ok=True)
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(FAISS_DOCS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.docs, f, ensure_ascii=False)

    # ─────────────────────────────────────────────
    # File reading
    # ─────────────────────────────────────────────

    async def _read_file_content(self, file) -> str:
        filename = file.filename.lower()
        raw_bytes = await file.read()

        if filename.endswith(".txt"):
            return raw_bytes.decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

        elif filename.endswith(".csv"):
            text_lines = []
            decoded = raw_bytes.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(decoded))
            for row in reader:
                line = " | ".join(f"{k}: {v}" for k, v in row.items())
                text_lines.append(line)
            return "\n".join(text_lines)

        else:
            raise ValueError(
                f"Unsupported file type: '{filename}'. Supported: .txt, .pdf, .csv"
            )

    # ─────────────────────────────────────────────
    # Ingest
    # ─────────────────────────────────────────────

    async def ingest(self, file) -> dict:
        content = await self._read_file_content(file)

        if not content.strip():
            return {"ingested_chunks": 0, "message": "File was empty or unreadable"}

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(content)

        # SentenceTransformer is synchronous — runs on CPU locally
        # encode() returns numpy array directly — no async needed
        vectors = self.model.encode(chunks, show_progress_bar=False)

        self.index.add(np.array(vectors, dtype="float32"))
        self.docs.extend(chunks)
        self._save_to_disk()

        return {
            "ingested_chunks": len(chunks),
            "total_chunks_in_index": len(self.docs),
            "filename": file.filename
        }

    # ─────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────

    async def search(self, query: str, top_k: int = 5) -> list[str]:
        if len(self.docs) == 0:
            return []

        # encode() returns 2D array — take first row for single query
        vector = self.model.encode([query], show_progress_bar=False)[0]
        _, indices = self.index.search(np.array([vector], dtype="float32"), top_k)
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]


# Singleton — created once at app startup
rag_service_instance = RAGService()
