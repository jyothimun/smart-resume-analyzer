"""Scoring engine: skill overlap + TF-IDF cosine similarity + resume quality."""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
from . import parser, skills as skill_dict

CORE_SECTIONS = ["education", "experience", "skills", "projects"]


def verdict_for(score: float) -> str:
    if score >= 75:
        return "Strong match"
    if score >= 55:
        return "Good match"
    if score >= 35:
        return "Partial match"
    return "Weak match"


def _text_similarity(job_text: str, resume_text: str):
    """Return (scaled 0-1 similarity, list of shared keywords)."""
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b[A-Za-z][A-Za-z+#.\-]{1,}\b")
    try:
        matrix = vec.fit_transform([job_text, resume_text])
    except ValueError:  # empty vocabulary
        return 0.0, []
    cos = float(cosine_similarity(matrix[0], matrix[1])[0][0])
    scaled = min(1.0, cos / 0.45)  # resumes rarely exceed ~0.45 cosine against a job post

    terms = vec.get_feature_names_out()
    jd_vec = matrix[0].toarray()[0]
    cv_vec = matrix[1].toarray()[0]
    shared = [(terms[i], jd_vec[i] * cv_vec[i]) for i in range(len(terms)) if jd_vec[i] > 0 and cv_vec[i] > 0]
    shared.sort(key=lambda t: t[1], reverse=True)
    keywords = []
    for term, _ in shared:
        if any(term in k or k in term for k in keywords):
            continue
        keywords.append(term)
        if len(keywords) == 10:
            break
    return scaled, keywords


def _quality(text: str, email, phone, sections):
    contact = (0.5 if email else 0) + (0.5 if phone else 0)
    section_part = len([s for s in CORE_SECTIONS if s in sections]) / len(CORE_SECTIONS)
    words = len(text.split())
    if 200 <= words <= 1500:
        length = 1.0
    elif 100 <= words < 200 or 1500 < words <= 2500:
        length = 0.6
    else:
        length = 0.3
    return 0.3 * contact + 0.5 * section_part + 0.2 * length


def analyze(job_description: str, job_skills: list, resume_text: str, filename: str = ""):
    """Score one resume against one job. Returns a dict ready to store."""
    required = job_skills or skill_dict.extract_skills(job_description)
    resume_skills = skill_dict.extract_skills(resume_text)

    matched = [s for s in required if skill_dict.has_skill(resume_text, s)]
    missing = [s for s in required if s not in matched]
    required_lower = {r.lower() for r in required}
    extra = [s for s in resume_skills if s.lower() not in required_lower][:14]

    text_sim, keywords = _text_similarity(job_description, resume_text)
    skill_ratio = (len(matched) / len(required)) if required else text_sim

    email = parser.find_email(resume_text)
    phone = parser.find_phone(resume_text)
    sections = parser.find_sections(resume_text)
    quality = _quality(resume_text, email, phone, sections)

    score = 100 * (config.W_SKILLS * skill_ratio + config.W_TEXT * text_sim + config.W_QUALITY * quality)
    score = round(max(0.0, min(100.0, score)), 1)

    return {
        "name": parser.find_name(resume_text, filename),
        "email": email,
        "phone": phone,
        "years_exp": parser.find_years(resume_text),
        "score": score,
        "skill_score": round(skill_ratio * 100, 1),
        "text_score": round(text_sim * 100, 1),
        "quality_score": round(quality * 100, 1),
        "verdict": verdict_for(score),
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "sections": sections,
        "keywords": keywords,
    }
