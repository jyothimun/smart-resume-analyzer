"""Smart Resume Screening System - Flask API (also serves the built React app)."""
import csv
import io
import json
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
import database as dbm
from services import ai_feedback, parser, scorer
from services import skills as skill_dict

config.UPLOAD_DIR.mkdir(exist_ok=True)
dbm.init_db()

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
CORS(app, resources={r"/api/*": {"origins": "*"}})


def error(message, status=400):
    return jsonify({"error": message}), status


@app.errorhandler(413)
def too_large(_):
    return error("Upload is too large. Keep the total under 60 MB.", 413)


@app.errorhandler(Exception)
def unexpected(exc):
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):
        return error(exc.description, exc.code)
    app.logger.exception("Unhandled error")
    return error("Something went wrong on the server. Check the backend terminal for details.", 500)


# ----------------------------------------------------------------------------- health
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "ai_enabled": bool(config.ANTHROPIC_API_KEY),
        "ai_model": config.ANTHROPIC_MODEL if config.ANTHROPIC_API_KEY else None,
    })


# ----------------------------------------------------------------------------- jobs
JOB_LIST_SQL = """
SELECT j.*, COUNT(c.id) AS n, MAX(c.score) AS top, AVG(c.score) AS avg
FROM jobs j LEFT JOIN candidates c ON c.job_id = j.id
{where}
GROUP BY j.id ORDER BY j.id DESC
"""


def _job_with_stats(conn, job_id):
    row = conn.execute(JOB_LIST_SQL.format(where="WHERE j.id = ?"), (job_id,)).fetchone()
    if not row:
        return None
    avg = round(row["avg"], 1) if row["avg"] is not None else None
    return dbm.job_row(row, row["n"], row["top"], avg)


@app.get("/api/jobs")
def list_jobs():
    with dbm.db() as conn:
        rows = conn.execute(JOB_LIST_SQL.format(where="")).fetchall()
    return jsonify([
        dbm.job_row(r, r["n"], r["top"], round(r["avg"], 1) if r["avg"] is not None else None)
        for r in rows
    ])


@app.post("/api/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title:
        return error("Add a job title.")
    if len(description.split()) < 15:
        return error("Paste the full job description (at least 15 words) so resumes can be matched to it.")

    given = data.get("skills")
    if isinstance(given, str):
        given = [s for s in (x.strip() for x in given.split(",")) if s]
    skills = skill_dict.normalize_skill_list(given) or skill_dict.extract_skills(description)

    with dbm.db() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (title, description, skills_json) VALUES (?, ?, ?)",
            (title, description, json.dumps(skills)),
        )
        job = _job_with_stats(conn, cur.lastrowid)
    return jsonify(job), 201


@app.get("/api/jobs/<int:job_id>")
def get_job(job_id):
    with dbm.db() as conn:
        job = _job_with_stats(conn, job_id)
        if not job:
            return error("Job not found.", 404)
        rows = conn.execute(
            "SELECT * FROM candidates WHERE job_id = ? ORDER BY score DESC, id ASC", (job_id,)
        ).fetchall()
    job["candidates"] = [dbm.candidate_row(r) for r in rows]
    return jsonify(job)


@app.delete("/api/jobs/<int:job_id>")
def delete_job(job_id):
    with dbm.db() as conn:
        cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    if cur.rowcount == 0:
        return error("Job not found.", 404)
    return jsonify({"deleted": job_id})


# ----------------------------------------------------------------------------- resumes
def _score_and_store(conn, job, filename, text):
    result = scorer.analyze(job["description"], job["skills"], text, filename)
    cur = conn.execute(
        """INSERT INTO candidates
           (job_id, filename, name, email, phone, years_exp, score, skill_score, text_score,
            quality_score, verdict, matched_json, missing_json, extra_json, sections_json,
            keywords_json, resume_text)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            job["id"], filename, result["name"], result["email"], result["phone"], result["years_exp"],
            result["score"], result["skill_score"], result["text_score"], result["quality_score"],
            result["verdict"], json.dumps(result["matched"]), json.dumps(result["missing"]),
            json.dumps(result["extra"]), json.dumps(result["sections"]), json.dumps(result["keywords"]),
            text,
        ),
    )
    row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dbm.candidate_row(row)


@app.post("/api/jobs/<int:job_id>/resumes")
def upload_resumes(job_id):
    files = request.files.getlist("files")
    if not files:
        return error("Choose at least one resume file (PDF, DOCX or TXT).")

    with dbm.db() as conn:
        job = _job_with_stats(conn, job_id)
    if not job:
        return error("Job not found.", 404)

    added, errors = [], []
    for f in files:
        original = f.filename or "resume"
        ext = Path(original).suffix.lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            errors.append({"filename": original, "error": "Only PDF, DOCX and TXT files are supported."})
            continue
        saved = config.UPLOAD_DIR / f"{uuid.uuid4().hex}_{secure_filename(original) or 'resume' + ext}"
        f.save(saved)
        try:
            text = parser.extract_text(saved)
            with dbm.db() as conn:
                added.append(_score_and_store(conn, job, original, text))
        except parser.ResumeParseError as exc:
            errors.append({"filename": original, "error": str(exc)})
            saved.unlink(missing_ok=True)

    status = 201 if added else 422
    return jsonify({"added": added, "errors": errors}), status


@app.get("/api/candidates/<int:cid>")
def get_candidate(cid):
    with dbm.db() as conn:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cid,)).fetchone()
    if not row:
        return error("Candidate not found.", 404)
    return jsonify(dbm.candidate_row(row, full=True))


@app.delete("/api/candidates/<int:cid>")
def delete_candidate(cid):
    with dbm.db() as conn:
        cur = conn.execute("DELETE FROM candidates WHERE id = ?", (cid,))
    if cur.rowcount == 0:
        return error("Candidate not found.", 404)
    return jsonify({"deleted": cid})


@app.post("/api/candidates/<int:cid>/insights")
def candidate_insights(cid):
    with dbm.db() as conn:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cid,)).fetchone()
        if not row:
            return error("Candidate not found.", 404)
        job = _job_with_stats(conn, row["job_id"])
        cand = dbm.candidate_row(row)
        text, source = ai_feedback.generate(job, cand, row["resume_text"])
        conn.execute("UPDATE candidates SET insights = ?, insights_src = ? WHERE id = ?", (text, source, cid))
    return jsonify({"insights": text, "insights_src": source})


@app.get("/api/jobs/<int:job_id>/export.csv")
def export_csv(job_id):
    with dbm.db() as conn:
        job = _job_with_stats(conn, job_id)
        if not job:
            return error("Job not found.", 404)
        rows = conn.execute(
            "SELECT * FROM candidates WHERE job_id = ? ORDER BY score DESC", (job_id,)
        ).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Name", "Email", "Phone", "Score", "Verdict", "Skill match %", "Text match %",
                "Matched skills", "Missing skills", "File"])
    for i, r in enumerate(rows, 1):
        c = dbm.candidate_row(r)
        w.writerow([i, c["name"], c["email"] or "", c["phone"] or "", c["score"], c["verdict"],
                    c["skill_score"], c["text_score"], "; ".join(c["matched"]), "; ".join(c["missing"]),
                    c["filename"]])
    name = secure_filename(job["title"]) or "job"
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={name}_ranking.csv"},
    )


# ----------------------------------------------------------------------------- demo data
SAMPLES_DIR = config.BASE_DIR.parent / "samples"


@app.post("/api/demo")
def load_demo():
    jd_file = SAMPLES_DIR / "job_description.txt"
    resumes = sorted(SAMPLES_DIR.glob("resume_*.txt"))
    if not jd_file.exists() or not resumes:
        return error("Sample files are missing. Expected a 'samples' folder next to 'backend'.", 404)
    lines = jd_file.read_text(encoding="utf-8").strip().splitlines()
    title = lines[0].replace("Title:", "").strip()
    description = "\n".join(lines[1:]).strip()
    skills = skill_dict.extract_skills(description)
    with dbm.db() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (title, description, skills_json) VALUES (?, ?, ?)",
            (title, description, json.dumps(skills)),
        )
        job = _job_with_stats(conn, cur.lastrowid)
        for path in resumes:
            text = parser.clean_text(path.read_text(encoding="utf-8"))
            _score_and_store(conn, job, path.name, text)
        job = _job_with_stats(conn, job["id"])
    return jsonify(job), 201


# ----------------------------------------------------------------------------- frontend (built React app)
@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def frontend(path):
    if path.startswith("api/"):
        return error("Unknown API route.", 404)
    if not (config.STATIC_DIR / "index.html").exists():
        return Response(
            "<h2>Backend is running.</h2><p>The React app is not built yet. "
            "Run <code>npm install &amp;&amp; npm run dev</code> inside the <b>frontend</b> folder "
            "and open http://localhost:5173, or run <code>npm run build</code> to serve it from here.</p>",
            mimetype="text/html",
        )
    target = config.STATIC_DIR / path
    if path and target.is_file():
        return send_from_directory(config.STATIC_DIR, path)
    return send_from_directory(config.STATIC_DIR, "index.html")


if __name__ == "__main__":
    print(f"\n  Smart Resume Screener running at http://localhost:{config.PORT}\n"
          f"  AI insights: {'Claude (' + config.ANTHROPIC_MODEL + ')' if config.ANTHROPIC_API_KEY else 'built-in rules (add ANTHROPIC_API_KEY to backend/.env for Claude)'}\n")
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
