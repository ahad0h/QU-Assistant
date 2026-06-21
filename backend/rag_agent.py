"""
RAG Agent - Qassim University College of Computer
Agentic RAG pipeline using FAISS + SentenceTransformers + Groq LLM.
"""

import os, re, json, pickle
import numpy as np
import requests as req
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from groq import Groq
from bs4 import BeautifulSoup

# ============================================================
# Config
# ============================================================
PDF_FOLDER       = os.getenv("PDF_FOLDER", "./pdfs")
INDEX_DIR        = os.getenv("INDEX_DIR", "./rag_index")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL        = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
TOP_K            = 5
CHUNK_SIZE       = 900
OVERLAP          = 150

PDF_URLS = [
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/Academic-Advising-Handbook-CS.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/CS-GP-Guide_COC_QU_v2-1.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/CS_ST_Guide_COC_QU.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/1-1-1-13-Student-Handbook.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/BSC-CS-Courses-Specifications.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/1-1-1-15-Organizational-and-Procedural-Guide-for-Administrative-Tasks-in-the-Departments-of-the-College-of-Computer.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/1-1-1-12-Academic-Program-Handbook-for-Faculty-Members_17_01.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/Program-Update-and-Review-Procedures-Guide.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/09/1-2-1-2-Quality_Manual_Managment_System.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/Quality_Manual_Managment_System-1.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/CSC-Master-Academic-Advising-Handbook.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/IT_Academic_Program_Handbook_for_Faculty.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/IT_Quality_Manual_Managment_System.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/COE-Student-Handbook.pdf",
    "https://www.qu.edu.sa/wp-content/uploads/2025/10/Masters-Student-Handbook.pdf",
]

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

QU_PAGES = [
    ("https://www.qu.edu.sa/about/", "\u0639\u0646 \u0627\u0644\u062c\u0627\u0645\u0639\u0629"),
    ("https://www.qu.edu.sa/university-president/cv/", "\u0631\u0626\u064a\u0633 \u0627\u0644\u062c\u0627\u0645\u0639\u0629"),
    ("https://www.qu.edu.sa/colleges/coc/about/", "\u0639\u0646 \u0643\u0644\u064a\u0629 \u0627\u0644\u062d\u0627\u0633\u0628"),
    ("https://www.qu.edu.sa/colleges/coc/departments/coc-2/", "\u0642\u0633\u0645 \u0639\u0644\u0648\u0645 \u0627\u0644\u062d\u0627\u0633\u0628"),
    ("https://www.qu.edu.sa/colleges/coc/departments/coc-3/", "\u0642\u0633\u0645 \u062a\u0642\u0646\u064a\u0629 \u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a"),
    ("https://www.qu.edu.sa/colleges/coc/departments/coc-1/", "\u0642\u0633\u0645 \u0647\u0646\u062f\u0633\u0629 \u0627\u0644\u062d\u0627\u0633\u0628"),
    ("https://www.qu.edu.sa/colleges/coc/departments/coc-4/", "\u0642\u0633\u0645 \u0627\u0644\u0623\u0645\u0646 \u0627\u0644\u0633\u064a\u0628\u0631\u0627\u0646\u064a"),
    ("https://www.qu.edu.sa/colleges/coc/programs/", "\u0628\u0631\u0627\u0645\u062c \u0627\u0644\u0643\u0644\u064a\u0629"),
    ("https://www.qu.edu.sa/about/vision/", "\u0631\u0624\u064a\u0629 \u0627\u0644\u062c\u0627\u0645\u0639\u0629 \u0648\u0631\u0633\u0627\u0644\u062a\u0647\u0627"),
    ("https://www.qu.edu.sa/about/history/", "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u062c\u0627\u0645\u0639\u0629"),
]

# ============================================================
# Global state
# ============================================================
emb_model   = None
faiss_index = None
corpus      = []
groq_client = None

# ============================================================
# Helpers
# ============================================================
def _ua_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ar,en;q=0.9",
    }

def download_pdfs_from_urls(url_list, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    for url in url_list:
        filename = url.split("/")[-1]
        filepath = os.path.join(target_folder, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            continue
        try:
            r = req.get(url, timeout=60)
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
            print("  [download] " + filename)
        except Exception as e:
            print("  Failed to download " + filename + ": " + str(e))

def scrape_qu_pages(target_folder):
    os.makedirs(target_folder, exist_ok=True)
    for url, label in QU_PAGES:
        try:
            r = req.get(url, headers=_ua_headers(), timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["nav", "footer", "header", "script", "style", "aside"]):
                tag.decompose()
            main = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup
            text = main.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 30]
            clean = "\n".join(lines[:200])
            if len(clean) < 100:
                continue
            fname = url.replace("https://www.qu.edu.sa/", "").replace("/", "_").strip("_") + ".txt"
            source_line = "# \u0627\u0644\u0645\u0635\u062f\u0631: " + url
            with open(os.path.join(target_folder, fname), "w", encoding="utf-8") as f:
                f.write("# " + label + "\n" + source_line + "\n\n" + clean)
            PDF_METADATA.setdefault(fname, {"department": "all", "level": "all", "type": "university_info"})
        except Exception as e:
            print("  [" + label + "] failed: " + str(e))

def clean_text(text):
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return " ".join(text.split()).strip()

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = clean_text(page.extract_text() or "")
            if text:
                pages.append((text, i + 1))
        return pages
    except Exception as e:
        print("  Could not read " + pdf_path + ": " + str(e))
        return []

def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = clean_text(f.read())
        return [(text, 1)] if text else []
    except Exception as e:
        print("  Could not read " + txt_path + ": " + str(e))
        return []

def chunk_text_smart(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            boundary = text.rfind('. ', start, end)
            if boundary != -1 and boundary > start + overlap:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def build_corpus(folder):
    out = []
    files = sorted(f for f in os.listdir(folder) if f.endswith((".pdf", ".txt")))
    for fname in files:
        path = os.path.join(folder, fname)
        meta = PDF_METADATA.get(fname, {"department": "all", "level": "all", "type": "general"})
        pages = extract_text_from_pdf(path) if fname.endswith(".pdf") else extract_text_from_txt(path)
        if not pages:
            continue
        for page_text, page_num in pages:
            for ch in chunk_text_smart(page_text):
                out.append({"text": ch, "source": fname, "page": page_num, **meta})
    return out

def embed_texts(model, texts, batch_size=32):
    emb = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
    return (emb / norms).astype("float32")

def build_faiss_index(embeddings):
    idx = faiss.IndexFlatIP(embeddings.shape[1])
    idx.add(embeddings)
    return idx

def save_index(idx, corp):
    os.makedirs(INDEX_DIR, exist_ok=True)
    faiss.write_index(idx, os.path.join(INDEX_DIR, "index.faiss"))
    with open(os.path.join(INDEX_DIR, "corpus.pkl"), "wb") as f:
        pickle.dump(corp, f)

def load_index():
    idx = faiss.read_index(os.path.join(INDEX_DIR, "index.faiss"))
    with open(os.path.join(INDEX_DIR, "corpus.pkl"), "rb") as f:
        corp = pickle.load(f)
    return idx, corp

# ============================================================
# Index initialization
# ============================================================
def init_index(force_rebuild: bool = False):
    global emb_model, faiss_index, corpus, groq_client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment variables")
    groq_client = Groq(api_key=api_key)

    emb_model = SentenceTransformer(EMBED_MODEL_NAME)

    index_path  = os.path.join(INDEX_DIR, "index.faiss")
    corpus_path = os.path.join(INDEX_DIR, "corpus.pkl")
    if not force_rebuild and os.path.exists(index_path) and os.path.exists(corpus_path):
        faiss_index, corpus = load_index()
        print("Index loaded - " + str(len(corpus)) + " chunks")
        return

    print("=== Building index from scratch ===")
    os.makedirs(PDF_FOLDER, exist_ok=True)
    download_pdfs_from_urls(PDF_URLS, PDF_FOLDER)
    scrape_qu_pages(PDF_FOLDER)
    corpus = build_corpus(PDF_FOLDER)
    print("  total chunks: " + str(len(corpus)))
    embeddings = embed_texts(emb_model, [c["text"] for c in corpus])
    faiss_index = build_faiss_index(embeddings)
    save_index(faiss_index, corpus)
    print("Index ready - " + str(len(corpus)) + " chunks")

# ============================================================
# Agents
# ============================================================
def call_llm(prompt, temperature=0.1, max_tokens=500):
    resp = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def format_context(results, max_chars=7000):
    parts, used = [], 0
    for i, (ch, score) in enumerate(results, 1):
        block = "[" + str(i) + "] Source: " + ch['source'] + " (page " + str(ch['page']) + ") | score=" + str(round(score, 3)) + "\n" + ch['text'] + "\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n---\n".join(parts)

def query_analysis_agent(question, department_override=None, level_override=None):
    prompt = (
        "You are an academic query analysis agent for Qassim University College of Computer.\n"
        "Analyze the question and return a JSON with:\n"
        '- "intent": one of ["information", "procedure", "requirement", "general"]\n'
        '- "topic": one of ["graduation_project", "courses", "internship", "handbook", "advising", "general"]\n'
        '- "department": one of ["CS", "IT", "CE", "all"]\n'
        '- "level": one of ["bachelor", "master", "all"]\n'
        '- "refined_query": a clear English version optimized for document search\n\n'
        "QUESTION: " + question + "\n"
        "Return ONLY the JSON. No markdown."
    )
    raw = call_llm(prompt, temperature=0.0, max_tokens=256)
    try:
        info = json.loads(re.sub(r"```json|```", "", raw).strip())
    except Exception:
        info = {"intent": "general", "topic": "general", "department": "all",
                "level": "all", "refined_query": question}
    if department_override and department_override.lower() != "all":
        info["department"] = department_override.upper()
    if level_override and level_override.lower() != "all":
        info["level"] = level_override.lower()
    return info

def retrieval_agent(query_info, top_k=TOP_K):
    refined_query = query_info.get("refined_query", "")
    department    = query_info.get("department", "all")
    level         = query_info.get("level", "all")
    topic         = query_info.get("topic", "general")

    q_emb = embed_texts(emb_model, [refined_query], batch_size=1)
    scores, idxs = faiss_index.search(q_emb, top_k * 4)
    candidates = [(corpus[idx], float(sc)) for sc, idx in zip(scores[0], idxs[0]) if idx != -1]

    def matches(ch):
        dept_ok  = department == "all" or ch.get("department") in [department, "all"]
        level_ok = level == "all"      or ch.get("level")      in [level, "all"]
        topic_ok = topic == "general"  or ch.get("type")       in [topic, "handbook"]
        return dept_ok and level_ok and topic_ok

    filtered = [(ch, sc) for ch, sc in candidates if matches(ch)]
    return (filtered if filtered else candidates)[:top_k]

def response_generation_agent(context, question, query_info, history=None, student_info=None):
    intent = query_info.get("intent", "general")
    topic  = query_info.get("topic",  "general")

    student_ctx = ""
    if student_info:
        if student_info.get("name"):       student_ctx += "Student name: " + student_info['name'] + ". "
        if student_info.get("department"): student_ctx += "Student department: " + student_info['department'] + ". "
        if student_info.get("level"):      student_ctx += "Student level: " + student_info['level'] + ". "

    history_ctx = ""
    if history:
        for h in history[-4:]:
            user_line = "User: " + h.get('q', '')
            logos_line = "\u0644\u0648\u062c\u0648\u0633: " + h.get('a', '')
            history_ctx += user_line + "\n" + logos_line + "\n"

    student_section = ("Student context: " + student_ctx + "\n") if student_ctx else ""
    history_section = ("Recent conversation:\n" + history_ctx + "\n") if history_ctx else ""

    prompt = (
        'You are "\u0644\u0648\u062c\u0648\u0633", a friendly and smart academic assistant for the College of Computer at Qassim University.\n\n'
        "Your personality:\n"
        "- Warm and conversational, like a helpful senior student\n"
        "- If greeted, greet back naturally (don't re-introduce yourself)\n"
        "- If question is vague, ask for clarification kindly\n"
        "- Use encouraging phrases when appropriate\n"
        "- Keep answers concise (3-4 sentences max)\n\n"
        "CRITICAL RULES:\n"
        "1. Answer ONLY using the CONTEXT below\n"
        "2. If the CONTEXT doesn't contain the answer, say (in the SAME language as the QUESTION) that this question is outside the scope of the academic service, and that you can only answer questions related to courses and regulations of the College of Computer at Qassim University\n"
        "3. NEVER use your general knowledge if the answer is not in the CONTEXT\n"
        "4. Cite sources as [1], [2], etc.\n\n"
        "LANGUAGE RULE:\n"
        "Detect the language the QUESTION is written in and respond ONLY in that exact language, including rule 2's fallback message.\n"
        "Never mix languages in your answer.\n\n"
        + student_section
        + history_section
        + "Intent: " + intent + ". Topic: " + topic + ".\n"
        "If intent is 'procedure' - list steps clearly.\n"
        "If intent is 'requirement' - list requirements clearly.\n\n"
        "CONTEXT:\n" + context + "\n\n"
        "QUESTION: " + question + "\n\n"
        "ANSWER:"
    )
    return call_llm(prompt, temperature=0.2, max_tokens=500)

def verification_agent(context, question, answer):
    prompt = (
        "You are a verification agent. Check if the ANSWER is fully supported by the CONTEXT.\n"
        "Return ONLY a JSON object with:\n"
        '- "verified": true if answer is grounded in context, false otherwise\n'
        '- "confidence": "high" / "medium" / "low"\n'
        '- "note": one-sentence explanation\n'
        "Return ONLY JSON. No markdown.\n\n"
        "CONTEXT:\n" + context + "\n\n"
        "QUESTION: " + question + "\n\n"
        "ANSWER: " + answer
    )
    raw = call_llm(prompt, temperature=0.0, max_tokens=200)
    try:
        return json.loads(re.sub(r"```json|```", "", raw).strip())
    except Exception:
        return {"verified": True, "confidence": "medium", "note": "Verification parsing failed."}

def agentic_pipeline(question, department=None, level=None, history=None, student_info=None):
    if student_info:
        department = department or student_info.get("department")
        level      = level      or student_info.get("level")

    query_info   = query_analysis_agent(question, department, level)
    results      = retrieval_agent(query_info)
    context      = format_context(results)
    answer       = response_generation_agent(context, question, query_info, history=history, student_info=student_info)
    verification = verification_agent(context, question, answer)

    if verification.get("confidence") == "low" and len(results) < 2:
        broad = dict(query_info, department="all", level="all", topic="general")
        fb_results = retrieval_agent(broad)
        if fb_results:
            fb_context = format_context(fb_results)
            answer       = response_generation_agent(fb_context, question, broad, history=history, student_info=student_info)
            verification = verification_agent(fb_context, question, answer)
            results = fb_results

    return {
        "answer":     answer,
        "verified":   verification.get("verified", True),
        "confidence": verification.get("confidence", "medium"),
        "note":       verification.get("note", ""),
        "query_info": query_info,
        "sources": [
            {"source": ch["source"], "page": ch["page"], "score": round(sc, 3)}
            for ch, sc in results
        ],
    }