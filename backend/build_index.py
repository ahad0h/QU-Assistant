import os, sys, re, pickle
import numpy as np
import faiss
from pypdf import PdfReader
from fastembed import TextEmbedding

# ============================================================
# Config
# ============================================================
PDF_DIR = os.path.join(os.path.dirname(__file__), "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
INDEX_DIR  = "./rag_index"
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 900
OVERLAP    = 150

PDF_METADATA = {
    "Academic-Advising-Handbook-CS.pdf":                {"department": "CS",  "level": "bachelor", "type": "advising"},
    "CS-GP-Guide_COC_QU_v2-1.pdf":                      {"department": "CS",  "level": "bachelor", "type": "graduation_project"},
    "CS_ST_Guide_COC_QU.pdf":                           {"department": "CS",  "level": "bachelor", "type": "internship"},
    "1-1-1-13-Student-Handbook.pdf":                    {"department": "all", "level": "all",      "type": "handbook"},
    "BSC-CS-Courses-Specifications.pdf":                {"department": "CS",  "level": "bachelor", "type": "courses"},
    "1-1-1-15-Organizational-and-Procedural-Guide-for-Administrative-Tasks-in-the-Departments-of-the-College-of-Computer.pdf": {"department": "all", "level": "all", "type": "admin_guide"},
    "1-1-1-12-Academic-Program-Handbook-for-Faculty-Members_17_01.pdf": {"department": "CS", "level": "all", "type": "faculty_handbook"},
    "Program-Update-and-Review-Procedures-Guide.pdf":   {"department": "CS",  "level": "all",     "type": "procedures"},
    "1-2-1-2-Quality_Manual_Managment_System.pdf":      {"department": "CS",  "level": "bachelor","type": "quality"},
    "Quality_Manual_Managment_System-1.pdf":            {"department": "CS",  "level": "master",  "type": "quality"},
    "CSC-Master-Academic-Advising-Handbook.pdf":        {"department": "CS",  "level": "master",  "type": "advising"},
    "IT_Academic_Program_Handbook_for_Faculty.pdf":     {"department": "IT",  "level": "all",     "type": "faculty_handbook"},
    "IT_Quality_Manual_Managment_System.pdf":           {"department": "IT",  "level": "bachelor","type": "quality"},
    "COE-Student-Handbook.pdf":                         {"department": "CE",  "level": "bachelor","type": "handbook"},
    "Masters-Student-Handbook.pdf":                     {"department": "CS",  "level": "master",  "type": "handbook"},
}

def clean_text(text):
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return " ".join(text.split()).strip()

def chunk_text_smart(text):
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + CHUNK_SIZE, n)
        if end < n:
            boundary = text.rfind('. ', start, end)
            if boundary != -1 and boundary > start + OVERLAP:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (CHUNK_SIZE - OVERLAP)
    return chunks

def build_corpus(folder):
    out = []
    files = sorted(f for f in os.listdir(folder) if f.endswith((".pdf", ".txt")))
    for fname in files:
        path = os.path.join(folder, fname)
        meta = PDF_METADATA.get(fname, {"department": "all", "level": "all", "type": "general"})
        if fname.endswith(".pdf"):
            try:
                reader = PdfReader(path)
                for i, page in enumerate(reader.pages):
                    text = clean_text(page.extract_text() or "")
                    if text:
                        for ch in chunk_text_smart(text):
                            out.append({"text": ch, "source": fname, "page": i+1, **meta})
            except Exception as e:
                print("  error: " + fname + " - " + str(e))
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = clean_text(f.read())
                if text:
                    for ch in chunk_text_smart(text):
                        out.append({"text": ch, "source": fname, "page": 1, **meta})
            except Exception as e:
                print("  error: " + fname + " - " + str(e))
    return out

# ============================================================
# Main
# ============================================================
print("Loading embedding model...")
emb_model = TextEmbedding(EMBED_MODEL_NAME)

print("Building corpus from local files...")
corpus = build_corpus(PDF_DIR)
print("Total chunks: " + str(len(corpus)))

print("Embedding chunks (this may take a few minutes)...")
texts = [c["text"] for c in corpus]
embeddings = list(emb_model.embed(texts))
emb = np.array(embeddings).astype("float32")
norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
emb = (emb / norms).astype("float32")

print("Building FAISS index...")
idx = faiss.IndexFlatIP(emb.shape[1])
idx.add(emb)

os.makedirs(INDEX_DIR, exist_ok=True)
faiss.write_index(idx, os.path.join(INDEX_DIR, "index.faiss"))
with open(os.path.join(INDEX_DIR, "corpus.pkl"), "wb") as f:
    pickle.dump(corpus, f)

print("Done! Index saved - " + str(len(corpus)) + " chunks")
