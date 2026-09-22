from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.rag_service import rag_service_instance

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (TXT, PDF, CSV) into the RAG system.

    What happens:
      - File is read and parsed based on type
      - Text is split into chunks
      - Chunks are converted to vectors and stored in FAISS

    Before (broken):
      rag = RAGService()   ← new instance every request, data lost immediately

    After (fixed):
      rag_service_instance ← shared singleton, data stays in memory
    """
    try:
        result = await rag_service_instance.ingest(file)
        return result
    except ValueError as e:
        # Unsupported file type
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/search")
async def search_documents(query: str):
    """
    Search across all uploaded documents for chunks relevant to the query.

    What happens:
      - Query is converted to a vector
      - FAISS finds the most similar stored vectors
      - Original text chunks are returned

    Uses the same rag_service_instance as upload —
    so it searches the SAME FAISS index where data was stored.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = await rag_service_instance.search(query)

    if not results:
        return {
            "query": query,
            "results": [],
            "message": "No results found. Make sure documents are uploaded first."
        }

    return {
        "query": query,
        "results": results
    }


@router.get("/status")
async def rag_status():
    """
    Returns how many chunks are currently stored in the RAG index.
    Useful to verify documents were ingested correctly.
    """
    return {
        "total_chunks": len(rag_service_instance.docs),
        "ready": len(rag_service_instance.docs) > 0
    }
