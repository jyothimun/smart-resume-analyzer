"""Resume text extraction + light-weight field detection (name, email, phone, sections)."""
import re
from pathlib import Path

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3,5}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,5}(?!\d)")
YEARS_RE = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)

SECTION_HEADINGS = {
    "summary": ["summary", "objective", "profile", "about me", "career objective", "professional summary"],
    "education": ["education", "academics", "academic background", "qualifications"],
    "experience": ["experience", "work experience", "employment", "internship", "internships", "professional experience"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies"],
    "projects": ["projects", "academic projects", "personal projects", "project work"],
    "certifications": ["certifications", "certificates", "courses", "licenses"],
    "achievements": ["achievements", "awards", "accomplishments", "honors", "hackathons"],
}


class ResumeParseError(Exception):
    pass


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            import pdfplumber
            pages = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
            text = "\n".join(pages)
        elif ext == ".docx":
            import docx2txt
            text = docx2txt.process(str(path)) or ""
        elif ext == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            raise ResumeParseError(f"Unsupported file type: {ext}")
    except ResumeParseError:
        raise
    except Exception as exc:  # corrupt / encrypted files
        raise ResumeParseError(f"Could not read {path.name}: {exc}") from exc

    text = clean_text(text)
    if len(text.split()) < 20:
        raise ResumeParseError(
            f"{path.name} has almost no readable text. Scanned image PDFs are not supported yet."
        )
    return text


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def find_email(text: str):
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def find_phone(text: str):
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            return m.group(0).strip()
    return None


def find_name(text: str, filename: str = ""):
    """Guess the candidate name from the first few lines; fall back to the filename."""
    heading_words = {w for group in SECTION_HEADINGS.values() for w in group} | {"resume", "curriculum vitae", "cv"}
    for line in text.splitlines()[:8]:
        line = line.strip(" \t|-:•")
        if not line or "@" in line or any(ch.isdigit() for ch in line):
            continue
        if line.lower() in heading_words:
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'\-]+", w) for w in words):
            return " ".join(w.capitalize() if w.isupper() else w for w in words)
    stem = Path(filename).stem
    stem = re.sub(r"(?i)resume|cv|[_\-\d]+", " ", stem).strip()
    return stem.title() if stem else "Unknown candidate"


def find_years(text: str):
    """Largest 'N years' figure that sits near the word 'experience'."""
    best = None
    for m in YEARS_RE.finditer(text):
        window = text[max(0, m.start() - 60): m.end() + 60].lower()
        if "experience" in window or "exp" in window:
            val = float(m.group(1))
            if val <= 45:
                best = val if best is None else max(best, val)
    return best


def find_sections(text: str):
    found = []
    lines = [l.strip().strip(":").lower() for l in text.splitlines()]
    for section, names in SECTION_HEADINGS.items():
        for line in lines:
            if 0 < len(line) <= 40 and line in names:
                found.append(section)
                break
    return found
