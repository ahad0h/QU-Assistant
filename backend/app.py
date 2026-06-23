"""
FastAPI server — Academic RAG API for QU College of Computer.

تشغيل محلي:
    export GROQ_API_KEY=sk_...
    uvicorn app:app --host 0.0.0.0 --port 8000

على Render:
    Start Command:  uvicorn app:app --host 0.0.0.0 --port $PORT
    Environment:    GROQ_API_KEY = <مفتاحك>
"""

import os, datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import rag_agent
from rag_agent import init_index, agentic_pipeline, PDF_METADATA, PDF_FOLDER

app = FastAPI(
    title="Academic RAG API — QU College of Computer",
    description="Agentic RAG system for answering academic questions from official QU documents.",
    version="2.0.0",
)

# CORS — مفتوح بالكامل لأي مصدر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Startup — يحمّل/يبني الفهرس مرة واحدة
# ============================================================
@app.on_event("startup")
def _startup():
    init_index()

# ============================================================
# Schemas
# ============================================================
class AskRequest(BaseModel):
    question:   str
    department: Optional[str] = None
    level:      Optional[str] = None

class SourceItem(BaseModel):
    source: str
    page:   int
    score:  float

class AskResponse(BaseModel):
    answer:     str
    verified:   bool
    confidence: str
    note:       str
    sources:    List[SourceItem]
    query_info: dict

class FeedbackRequest(BaseModel):
    question: str
    answer:   str
    rating:   int
    comment:  Optional[str] = None

class DocumentInfo(BaseModel):
    filename:   str
    department: str
    level:      str
    type:       str

feedback_log: list = []

# ============================================================
# Endpoints
# ============================================================
@app.get("/", tags=["System"])
def root():
    return {"service": "QU Academic RAG API", "docs": "/docs", "health": "/health"}

@app.get("/health", tags=["System"])
def health_check():
    ready = rag_agent.faiss_index is not None
    return {
        "status":       "ok",
        "message":      "Academic RAG API is running ✅",
        "index_loaded": ready,
        "total_chunks": len(rag_agent.corpus) if ready else 0,
    }

@app.get("/documents", response_model=List[DocumentInfo], tags=["Documents"])
def list_documents():
    return [
        DocumentInfo(
            filename=fname,
            department=meta.get("department", "all"),
            level=meta.get("level", "all"),
            type=meta.get("type", "general"),
        )
        for fname, meta in PDF_METADATA.items()
    ]

@app.get("/file/{filename}", tags=["Documents"])
def get_file(filename: str):
    try:
        for f in os.listdir(PDF_FOLDER):
            if filename.lower().replace("%20", " ") in f.lower():
                return FileResponse(os.path.join(PDF_FOLDER, f))
        raise HTTPException(status_code=404, detail=f"No matching file for: {filename}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse, tags=["QA"])
def ask_question(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if rag_agent.faiss_index is None:
        raise HTTPException(status_code=503, detail="Index not loaded.")
    try:
        return agentic_pipeline(
            question=body.question,
            department=body.department,
            level=body.level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(body: FeedbackRequest):
    if not (1 <= body.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    feedback_log.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "question":  body.question,
        "answer":    body.answer,
        "rating":    body.rating,
        "comment":   body.comment or "",
    })
    return {"message": "Feedback received. Thank you!", "total_feedback": len(feedback_log)}

@app.get("/feedback/summary", tags=["Feedback"])
def feedback_summary():
    if not feedback_log:
        return {"total": 0, "average_rating": None, "entries": []}
    avg = round(sum(e["rating"] for e in feedback_log) / len(feedback_log), 2)
    return {"total": len(feedback_log), "average_rating": avg, "entries": feedback_log}
