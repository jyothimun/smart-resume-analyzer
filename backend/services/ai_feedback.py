"""Candidate insights. Uses Claude when ANTHROPIC_API_KEY is set, otherwise a rule-based writer."""
import requests

import config

API_URL = "https://api.anthropic.com/v1/messages"

FORMAT_HELP = """Reply in plain text using exactly these four headings, each followed by "- " bullet lines
(Summary is a single short paragraph, no bullets):
Summary:
Strengths:
Gaps:
Interview questions:
Keep the whole reply under 220 words. Be specific to this resume and job. No markdown symbols other than "- "."""


def _prompt(job, cand, resume_text):
    return (
        "You are a careful technical recruiter helping a hiring manager screen a resume.\n\n"
        f"JOB TITLE: {job['title']}\n"
        f"JOB DESCRIPTION:\n{job['description'][:3500]}\n\n"
        f"AUTOMATED SCREENING RESULT: overall {cand['score']}/100 ({cand['verdict']}). "
        f"Matched skills: {', '.join(cand['matched']) or 'none'}. "
        f"Missing skills: {', '.join(cand['missing']) or 'none'}.\n\n"
        f"RESUME TEXT:\n{resume_text[:6000]}\n\n"
        + FORMAT_HELP
    )


def _claude(job, cand, resume_text):
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config.ANTHROPIC_MODEL,
            "max_tokens": 700,
            "messages": [{"role": "user", "content": _prompt(job, cand, resume_text)}],
        },
        timeout=45,
    )
    resp.raise_for_status()
    blocks = resp.json().get("content", [])
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    if not text:
        raise ValueError("Empty response from model")
    return text


def _rule_based(job, cand):
    name = cand["name"] or "This candidate"
    total = len(cand["matched"]) + len(cand["missing"])
    lines = ["Summary:"]
    exp = f" with about {cand['years_exp']:g} years of stated experience" if cand.get("years_exp") else ""
    lines.append(
        f"{name} scores {cand['score']}/100 for {job['title']} ({cand['verdict'].lower()}){exp}. "
        f"They cover {len(cand['matched'])} of {total} required skills."
        if total else
        f"{name} scores {cand['score']}/100 for {job['title']} ({cand['verdict'].lower()}){exp}."
    )
    lines.append("Strengths:")
    if cand["matched"]:
        lines.append("- Matches required skills: " + ", ".join(cand["matched"][:8]))
    if cand["keywords"]:
        lines.append("- Resume language overlaps the job post: " + ", ".join(cand["keywords"][:5]))
    if cand["extra"]:
        lines.append("- Additional skills that may help: " + ", ".join(cand["extra"][:5]))
    if "projects" in cand["sections"]:
        lines.append("- Includes a projects section that can be discussed in the interview")
    if lines[-1] == "Strengths:":
        lines.append("- No strong signals found in the automated scan")
    lines.append("Gaps:")
    if cand["missing"]:
        lines.append("- Missing or not clearly shown: " + ", ".join(cand["missing"][:8]))
    for sec in ("experience", "projects", "education", "skills"):
        if sec not in cand["sections"]:
            lines.append(f"- No clear '{sec}' section detected, so the resume may be hard to scan")
    if lines[-1] == "Gaps:":
        lines.append("- No major gaps detected by the automated scan")
    lines.append("Interview questions:")
    for skill in (cand["matched"][:2] or ["your most relevant project"]):
        lines.append(f"- Walk me through a real project where you used {skill}. What went wrong and how did you fix it?")
    if cand["missing"]:
        lines.append(f"- The role needs {cand['missing'][0]}. How would you get productive with it in your first month?")
    return "\n".join(lines)


def generate(job, cand, resume_text):
    """Returns (text, source) where source is 'claude' or 'rules'."""
    if config.ANTHROPIC_API_KEY:
        try:
            return _claude(job, cand, resume_text), "claude"
        except Exception as exc:  # network, quota, bad key ...
            text = _rule_based(job, cand)
            return text + f"\n(Claude was unavailable: {type(exc).__name__}. Showing built-in insights.)", "rules"
    return _rule_based(job, cand), "rules"
