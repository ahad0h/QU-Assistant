# المساعد الأكاديمي — كلية الحاسب، جامعة القصيم

نظام RAG وكيل (Agentic) للإجابة عن أسئلة الطلاب من الوثائق الرسمية للكلية.

## هيكل المشروع

```
project/
├── backend/
│   ├── app.py             # FastAPI server (endpoints)
│   ├── rag_agent.py       # RAG pipeline + agents (analysis/retrieval/generation/verification)
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── script.js
    └── style.css
```

---

## 1) تشغيل الباكند محلياً

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # على Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GROQ_API_KEY="مفتاحك_من_groq"
uvicorn app:app --host 0.0.0.0 --port 8000
```

أول تشغيل سيقوم تلقائياً بـ:
1. تحميل جميع ملفات PDF من موقع الجامعة إلى `./pdfs`
2. كشط صفحات HTML العامة
3. تقطيع النص + embeddings + بناء فهرس FAISS في `./rag_index`

(التشغيلات اللاحقة تُحمّل الفهرس مباشرة في ثوانٍ).

Endpoints:
- `GET  /health` — تحقق من التشغيل
- `GET  /documents` — قائمة الوثائق المُفهرسة
- `POST /ask` — السؤال (مع `department` و `level` اختياريين)
- `POST /feedback` — تقييم الإجابة
- `GET  /docs` — Swagger UI تلقائي

---

## 2) تشغيل الواجهة محلياً

```bash
cd frontend
python -m http.server 5173
```

افتح `http://localhost:5173` وأدخل رابط الـ API (`http://localhost:8000`).

> أو عدّل `DEFAULT_API_URL` في أعلى `script.js` ليتصل تلقائياً.

---

## 3) النشر على Render

### الخطوة A — رفع المشروع على GitHub
```bash
cd project
git init && git add . && git commit -m "initial"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

### الخطوة B — نشر الباكند (Web Service)
1. ادخل [Render Dashboard](https://dashboard.render.com) → **New → Web Service**
2. اربط مستودع GitHub
3. الإعدادات:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** يفضّل Starter أو أعلى (الـ Free قد لا يكفي لتحميل نموذج التضمين)
4. **Environment Variables:**
   - `GROQ_API_KEY` = مفتاحك من https://console.groq.com/keys
   - (اختياري) `ALLOWED_ORIGINS` = رابط الـ frontend بعد نشره (لتقييد CORS)
5. اضغط **Create Web Service**. بعد الانتهاء ستحصل على رابط مثل:
   `https://qu-assistant-api.onrender.com`

> ⚠️ أول طلب بعد النشر قد يستغرق دقائق لبناء الفهرس. راقب الـ Logs.

### الخطوة C — نشر الواجهة (Static Site)
1. **New → Static Site** → نفس المستودع
2. الإعدادات:
   - **Root Directory:** `frontend`
   - **Build Command:** (اتركه فارغاً)
   - **Publish Directory:** `.`
3. **Create Static Site**. ستحصل على رابط مثل:
   `https://qu-assistant.onrender.com`

### الخطوة D — ربط الواجهة بالباكند
عدّل أول سطر في `frontend/script.js`:
```js
const DEFAULT_API_URL = "https://qu-assistant-api.onrender.com";
```
ثم اعمل push للتغيير — سيُعاد نشر الواجهة تلقائياً.

---

## ملاحظات أمنية

- لا تضع `GROQ_API_KEY` في الكود أو على GitHub أبداً. ضعه فقط في **Environment Variables** على Render.
- إن كنت قد شاركت المفتاح في محادثة سابقة، احذفه من https://console.groq.com/keys وأنشئ مفتاحاً جديداً.
- بعد النشر، قيّد `ALLOWED_ORIGINS` على رابط الـ frontend الخاص بك فقط بدل `*`.
