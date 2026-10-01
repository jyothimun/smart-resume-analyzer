# Smart Resume Screening System

An ATS-style web app. Create a job, drop in PDF / DOCX / TXT resumes, and get them ranked by how well they fit,
with a full breakdown for every candidate and optional Claude-written interview insights.

**Stack:** React (Vite, custom dark CSS) · Flask API · SQLite · scikit-learn (TF-IDF) · pdfplumber / docx2txt · optional Claude API

---

## Run it (easiest way)

The React app is already built and lives in `backend/static`, so you only need Python 3.10+.

**Windows:** double-click `run.bat`
**macOS / Linux:** `./run.sh`

Then open **http://localhost:5000**. On the first screen, click **Load demo data** to see six sample resumes ranked instantly.

### Manual start (same thing, step by step)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

## Develop the frontend (optional, needs Node 18+)

Use two terminals:

```bash
# Terminal 1 - API
cd backend && python app.py

# Terminal 2 - React with hot reload
cd frontend && npm install && npm run dev      # opens http://localhost:5173
```

After changing the UI, run `npm run build` inside `frontend` to refresh `backend/static`.

## Turn on Claude insights (optional)

1. Copy `backend/.env.example` to `backend/.env`
2. Put your key in `ANTHROPIC_API_KEY=`
3. Restart `python app.py`

The sidebar then shows "Claude insights on". Without a key, the **Generate insights** button uses a built-in
rule-based writer, so the app is fully usable offline.

## How scoring works

| Part | Weight | What it measures |
|---|---|---|
| Skill match | 55% | Share of the job's required skills found in the resume (dictionary of ~110 skills with aliases, e.g. `js` = JavaScript; MySQL counts toward SQL) |
| Wording similarity | 35% | TF-IDF (1-2 word phrases) cosine similarity between job description and resume |
| Resume quality | 10% | Email and phone present, education / experience / skills / projects sections, sensible length |

Verdicts: 75+ Strong · 55+ Good · 35+ Partial · below 35 Weak. Weights live in `backend/config.py`.
If you list required skills when creating a job, those are used; otherwise they are detected from the description.

## Project layout

```
resume-screener/
├── run.bat / run.sh            one-click start
├── samples/                    demo job + resumes (txt, pdf, docx to try uploads)
├── backend/
│   ├── app.py                  Flask routes + serves the built React app
│   ├── config.py, database.py  settings, SQLite schema
│   ├── services/
│   │   ├── parser.py           PDF/DOCX/TXT text, name/email/phone/sections
│   │   ├── skills.py           skill dictionary + matching
│   │   ├── scorer.py           TF-IDF + scoring
│   │   └── ai_feedback.py      Claude insights with rule-based fallback
│   ├── tests/test_scorer.py    python -m unittest discover -s tests
│   └── static/                 built frontend
└── frontend/                   React source (Vite)
    └── src/ App.jsx, api.js, styles.css, components/
```

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Status and whether Claude is enabled |
| GET / POST | `/api/jobs` | List jobs / create a job |
| GET / DELETE | `/api/jobs/<id>` | Job with ranked candidates / delete |
| POST | `/api/jobs/<id>/resumes` | Upload one or many resumes (`files` field) |
| GET | `/api/jobs/<id>/export.csv` | Download the ranking |
| GET / DELETE | `/api/candidates/<id>` | Candidate detail / remove |
| POST | `/api/candidates/<id>/insights` | Generate insights |
| POST | `/api/demo` | Load the sample job and resumes |

Data is stored in `backend/screener.db` (created on first run). Delete that file to reset everything.

## Troubleshooting

- **`pip install` fails on scikit-learn (Windows):** the requirements are unpinned on purpose so pip uses prebuilt wheels. Upgrade pip (`python -m pip install --upgrade pip`) and retry.
- **PowerShell blocks `activate`:** run `Set-ExecutionPolicy -Scope Process Bypass`, or use `cmd` instead.
- **"Couldn't reach the backend":** the Flask terminal isn't running or crashed. Start `python app.py` and check its output. If port 5000 is busy, set `PORT=5001` in `backend/.env`. In dev mode also change the proxy in `frontend/vite.config.js`.
- **A resume says "almost no readable text":** it is probably a scanned image PDF. OCR is not included.

## Ideas to extend

Semantic matching with `sentence-transformers`, login and per-user jobs, PDF report export, OCR for scanned resumes.
