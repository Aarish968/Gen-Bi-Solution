"""
rag_service.py

RAG (Retrieval-Augmented Generation) Service.

Responsibilities:
  - Ingest documents (TXT, PDF, CSV) → split into chunks → convert to vectors → store in FAISS
  - Search: convert user query to vector → find similar chunks → return original text

Singleton Pattern:
  - Only ONE instance of RAGService exists for the entire app lifetime
  - All upload and search requests share the same FAISS index

Persistence:
  - FAISS index saved to disk after every upload  → data/faiss_index.bin
  - Docs list saved to disk after every upload    → data/faiss_docs.json
  - On startup, both are loaded from disk if they exist
  - Server restart = data still there ✅

Supported file types:
  - .txt  → read directly as plain text
  - .pdf  → extract text from all pages using pypdf
  - .csv  → read rows and join as plain text
"""

import io
import os
import csv
import json
import faiss
import numpy as np
from pypdf import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

# Paths where FAISS index and docs are saved on disk
FAISS_INDEX_PATH = "data/faiss_index.bin"
FAISS_DOCS_PATH  = "data/faiss_docs.json"

# FAISS dimension for gemini-embedding-001
EMBEDDING_DIM = 3072


class RAGService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )

        # Load existing index + docs from disk if available
        # Otherwise start fresh
        self.index, self.docs = self._load_from_disk()

    # ─────────────────────────────────────────────
    # Persistence — save and load from disk
    # ─────────────────────────────────────────────

    def _load_from_disk(self):
        """
        Loads FAISS index and docs list from disk on startup.

        Why 2 separate files:
          - faiss_index.bin → stores the vectors (FAISS binary format)
          - faiss_docs.json → stores the original text chunks (JSON list)
          FAISS only stores numbers — not the original text.
          We need both to return meaningful results after search.

        If files don't exist (first run) → start with empty index and empty docs.
        """
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_DOCS_PATH):
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_DOCS_PATH, "r", encoding="utf-8") as f:
                docs = json.load(f)
            print(f"[RAGService] Loaded {len(docs)} chunks from disk.")
            return index, docs

        # First run — nothing on disk yet
        print("[RAGService] No existing index found. Starting fresh.")
        return faiss.IndexFlatL2(EMBEDDING_DIM), []

    def _save_to_disk(self):
        """
        Saves FAISS index and docs list to disk after every upload.

        Called at the end of ingest() so data is never lost
        even if the server restarts immediately after upload.
        """
        os.makedirs("data", exist_ok=True)
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(FAISS_DOCS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.docs, f, ensure_ascii=False)

    # ─────────────────────────────────────────────
    # File reading — supports TXT, PDF, CSV
    # ─────────────────────────────────────────────

    async def _read_file_content(self, file) -> str:
        """
        Reads uploaded file and returns plain text content.
        Supports: .txt, .pdf, .csv
        """
        filename = file.filename.lower()
        raw_bytes = await file.read()

        if filename.endswith(".txt"):
            return raw_bytes.decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            # Extract text from all pages
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

        elif filename.endswith(".csv"):
            # Each row becomes: "col1: val1 | col2: val2 | ..."
            text_lines = []
            decoded = raw_bytes.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(decoded))
            for row in reader:
                line = " | ".join(f"{k}: {v}" for k, v in row.items())
                text_lines.append(line)
            return "\n".join(text_lines)

        else:
            raise ValueError(
                f"Unsupported file type: '{filename}'. "
                "Supported types are: .txt, .pdf, .csv"
            )

    # ─────────────────────────────────────────────
    # Ingest — upload document into FAISS
    # ─────────────────────────────────────────────

    async def ingest(self, file) -> dict:
        """
        Reads file → splits into chunks → converts to vectors
        → stores in FAISS → saves to disk.

        Disk save happens at the end so data survives server restarts.
        """
        content = await self._read_file_content(file)

        if not content.strip():
            return {"ingested_chunks": 0, "message": "File was empty or unreadable"}

        # Split into overlapping chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(content)

        # Convert to vectors
        vectors = await self.embeddings.aembed_documents(chunks)

        # Store in FAISS
        self.index.add(np.array(vectors, dtype="float32"))
        self.docs.extend(chunks)

        # ── Save to disk so data survives server restart ──────────────────────
        self._save_to_disk()

        return {
            "ingested_chunks": len(chunks),
            "total_chunks_in_index": len(self.docs),
            "filename": file.filename
        }

    # ─────────────────────────────────────────────
    # Search — find relevant chunks for a query
    # ─────────────────────────────────────────────

    async def search(self, query: str, top_k: int = 5) -> list[str]:
        """
        Converts query to vector → searches FAISS → returns original text chunks.
        """
        if len(self.docs) == 0:
            return []

        vector = await self.embeddings.aembed_query(query)
        _, indices = self.index.search(np.array([vector], dtype="float32"), top_k)
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON INSTANCE
# Created once at app startup — loads existing data from disk automatically.
# ─────────────────────────────────────────────────────────────────────────────
rag_service_instance = RAGService()
