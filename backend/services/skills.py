"""Skill dictionary: canonical skill name -> list of aliases found in resumes / job posts."""
import re

SKILLS = {
    # Languages
    "Python": ["python", "python3"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "es6", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "C": ["c programming", "c language", "embedded c"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "Go": ["golang", "go lang"],
    "Rust": ["rust"],
    "PHP": ["php"],
    "Ruby": ["ruby"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "R": ["r programming", "rstudio"],
    "SQL": ["sql", "t-sql", "pl/sql", "plsql"],
    "Bash": ["bash", "shell scripting", "shell script"],
    # Web frontend
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Angular": ["angular", "angularjs"],
    "Vue": ["vue", "vue.js", "vuejs"],
    "Redux": ["redux"],
    "Tailwind CSS": ["tailwind", "tailwind css"],
    "Bootstrap": ["bootstrap"],
    "Vite": ["vite"],
    # Web backend
    "Node.js": ["node.js", "nodejs", "node js", "node"],
    "Express": ["express", "express.js", "expressjs"],
    "Flask": ["flask"],
    "Django": ["django"],
    "FastAPI": ["fastapi"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    ".NET": [".net", "dotnet", "asp.net"],
    "REST APIs": ["rest", "restful", "rest api", "rest apis", "restful api", "restful apis"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice"],
    # Databases
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb", "mongo"],
    "SQLite": ["sqlite", "sqlite3"],
    "Redis": ["redis"],
    "Firebase": ["firebase", "firestore"],
    "Oracle": ["oracle db", "oracle database"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    # ML / AI / Data
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "Keras": ["keras"],
    "PyTorch": ["pytorch", "torch"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Matplotlib": ["matplotlib"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Visualization": ["data visualization", "data visualisation"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Excel": ["excel", "ms excel", "microsoft excel"],
    "LLMs": ["llm", "llms", "large language models", "generative ai", "genai"],
    "Hugging Face": ["hugging face", "huggingface", "transformers"],
    "LangChain": ["langchain"],
    "Prompt Engineering": ["prompt engineering"],
    "Statistics": ["statistics", "statistical analysis"],
    "Spark": ["apache spark", "pyspark", "spark"],
    "Hadoop": ["hadoop"],
    # DevOps / Cloud
    "Git": ["git"],
    "GitHub": ["github"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3"],
    "Azure": ["azure"],
    "Google Cloud": ["gcp", "google cloud"],
    "CI/CD": ["ci/cd", "cicd", "ci cd", "jenkins", "github actions"],
    "Linux": ["linux", "ubuntu"],
    "Terraform": ["terraform"],
    "Nginx": ["nginx"],
    # Testing / process
    "Unit Testing": ["unit testing", "unit tests", "pytest", "junit", "jest"],
    "Selenium": ["selenium"],
    "Postman": ["postman"],
    "Agile": ["agile", "scrum", "kanban"],
    "Jira": ["jira"],
    "Figma": ["figma"],
    "Data Structures": ["data structures", "dsa"],
    "Algorithms": ["algorithms", "algorithm"],
    "OOP": ["oop", "oops", "object oriented", "object-oriented"],
    "System Design": ["system design"],
    "DBMS": ["dbms", "database management"],
    "Operating Systems": ["operating systems"],
    "Computer Networks": ["computer networks", "networking"],
    # Mobile
    "Android": ["android"],
    "Flutter": ["flutter"],
    "React Native": ["react native"],
    # Soft skills
    "Communication": ["communication", "communication skills"],
    "Teamwork": ["teamwork", "team player", "collaboration"],
    "Leadership": ["leadership", "team lead"],
    "Problem Solving": ["problem solving", "problem-solving"],
}

_BOUNDARY_L = r"(?<![A-Za-z0-9+#])"
_BOUNDARY_R = r"(?![A-Za-z0-9+#])"


def _compile():
    patterns = {}
    for canon, aliases in SKILLS.items():
        names = {a.lower() for a in aliases} | {canon.lower()}
        alt = "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True))
        patterns[canon] = re.compile(_BOUNDARY_L + "(?:" + alt + ")" + _BOUNDARY_R, re.IGNORECASE)
    return patterns


_PATTERNS = _compile()
_LOOKUP = {c.lower(): c for c in SKILLS}

# A required skill is also satisfied if the resume shows one of these more specific skills.
IMPLIED_BY = {
    "SQL": ["MySQL", "PostgreSQL", "SQLite", "Oracle"],
    "Machine Learning": ["scikit-learn", "TensorFlow", "PyTorch", "Keras", "Deep Learning"],
    "REST APIs": ["FastAPI", "Express", "Flask", "Django"],
}


def canonical(name: str):
    """Map a user-typed skill to its canonical name (or None if unknown)."""
    name = name.strip()
    if not name:
        return None
    if name.lower() in _LOOKUP:
        return _LOOKUP[name.lower()]
    for canon, pat in _PATTERNS.items():
        m = pat.fullmatch(name)
        if m:
            return canon
    return None


def extract_skills(text: str):
    """Return the list of canonical skills mentioned in text (dictionary order)."""
    return [canon for canon, pat in _PATTERNS.items() if pat.search(text)]


def has_skill(text: str, name: str) -> bool:
    """True if `name` (canonical or user-typed) appears in text."""
    canon = canonical(name)
    if canon:
        if _PATTERNS[canon].search(text):
            return True
        # e.g. knowing MySQL implies SQL
        return any(_PATTERNS[i].search(text) for i in IMPLIED_BY.get(canon, []))
    return bool(re.search(_BOUNDARY_L + re.escape(name.strip()) + _BOUNDARY_R, text, re.IGNORECASE))


def normalize_skill_list(items):
    """Clean a user-supplied skill list: canonical names where known, de-duplicated, order kept."""
    out, seen = [], set()
    for raw in items or []:
        raw = str(raw).strip()
        if not raw:
            continue
        name = canonical(raw) or raw
        if name.lower() not in seen:
            seen.add(name.lower())
            out.append(name)
    return out
