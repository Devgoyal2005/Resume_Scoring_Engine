import argparse
import json
import re
import math
from collections import Counter
from typing import Any, Dict, List, Tuple

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from sentence_transformers import SentenceTransformer, util
    NLTK_AVAILABLE = True
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    nltk = None
    stopwords = None
    WordNetLemmatizer = None
    SentenceTransformer = None
    util = None
    NLTK_AVAILABLE = False
    MODEL = None

NLTK_READY = False


WEIGHTS = {
    "required_qualifications": 0.35,
    "responsibilities": 0.25,
    "preferred_qualifications": 0.15,
    "skills": 0.15,
    "numeric_metrics": 0.10,
}

GENERIC_JOB_TERMS = {
    "looking", "engineer", "engineering", "software", "development", "developer",
    "experience", "required", "qualification", "preferred", "responsibility",
    "strong", "good", "knowledge", "understanding", "work", "working", "build",
    "team", "product", "customer", "system", "service", "services", "code",
    "clean", "maintainable", "scalable", "design", "develop", "year", "years",
}


def _ensure_nltk_resources() -> None:
    if not NLTK_AVAILABLE:
        return
    resources = [
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for resource_path, download_name in resources:
        try:
            nltk.data.find(resource_path)
        except LookupError:
            try:
                nltk.download(download_name, quiet=True)
            except Exception:
                # Corrupt local nltk cache or network errors: fallback later
                return
        except Exception:
            # Handles BadZipFile and any local cache corruption
            return


_ensure_nltk_resources()
if NLTK_AVAILABLE:
    try:
        STOP_WORDS = set(stopwords.words("english"))
        LEMMATIZER = WordNetLemmatizer()
        NLTK_READY = True
    except Exception:
        STOP_WORDS = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "were", "will", "with", "or", "this", "these", "those"
        }
        LEMMATIZER = None
        NLTK_READY = False
else:
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "were", "will", "with", "or", "this", "these", "those"
    }
    LEMMATIZER = None
    NLTK_READY = False


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    tokens = text.split()
    tokens = [w for w in tokens if w not in STOP_WORDS]
    if LEMMATIZER is not None and NLTK_READY:
        try:
            tokens = [LEMMATIZER.lemmatize(w) for w in tokens]
        except Exception:
            pass
    return " ".join(tokens)


def flatten_to_text(obj: Any) -> str:
    parts: List[str] = []

    def _walk(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, (int, float, bool)):
            parts.append(str(x))
        elif isinstance(x, list):
            for item in x:
                _walk(item)
        elif isinstance(x, dict):
            for v in x.values():
                _walk(v)

    _walk(obj)
    return " ".join(parts)


def semantic_score(text1: str, text2: str) -> float:
    """Computes semantic similarity using a sentence-transformer model."""
    if not text1.strip() or not text2.strip() or MODEL is None:
        return 0.0
    
    # Compute embedding for both texts
    embedding1 = MODEL.encode(text1, convert_to_tensor=True)
    embedding2 = MODEL.encode(text2, convert_to_tensor=True)
    
    # Compute cosine-similarity
    cosine_scores = util.cos_sim(embedding1, embedding2)
    return cosine_scores.item()


def keyword_score(job_section_text: str, resume_full_text: str) -> Tuple[float, List[str]]:
    """Calculates exact keyword match score."""
    job_tokens = set(normalize_text(job_section_text).split())
    resume_tokens = set(normalize_text(resume_full_text).split())
    
    if not job_tokens:
        return 0.0, []

    matched = sorted(list(job_tokens.intersection(resume_tokens)))
    score = len(matched) / len(job_tokens) if len(job_tokens) > 0 else 0.0
    return score, matched


def extract_critical_keywords(job_json: Dict[str, Any]) -> List[str]:
    """Build a focused keyword set from important JD sections."""
    important_parts = []
    important_parts.extend(job_json.get("skills", []) or [])
    important_parts.extend(job_json.get("required_qualifications", []) or [])
    important_parts.extend(job_json.get("preferred_qualifications", []) or [])
    important_parts.extend(job_json.get("responsibilities", []) or [])

    text = normalize_text(" ".join(important_parts))
    tokens = []
    for t in text.split():
        if len(t) < 3:
            continue
        if t in GENERIC_JOB_TERMS:
            continue
        tokens.append(t)
    return sorted(set(tokens))


def compute_ats_score(job_json: Dict[str, Any], resume_json: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Extract and prepare text sections from resume
    resume_full_text = flatten_to_text(resume_json)
    resume_experience_text = flatten_to_text(resume_json.get("experience", []))
    resume_projects_text = flatten_to_text(resume_json.get("projects", []))
    resume_skills_text = flatten_to_text(resume_json.get("skills", {}))
    resume_work_text = " ".join([resume_experience_text, resume_projects_text])

    # 2. Extract text sections from job description
    jd_req_qual_text = flatten_to_text(job_json.get("required_qualifications", []))
    jd_resp_text = flatten_to_text(job_json.get("responsibilities", []))
    jd_pref_qual_text = flatten_to_text(job_json.get("preferred_qualifications", []))
    jd_skills_text = flatten_to_text(job_json.get("skills", []))

    # 3. Calculate component scores based on the hybrid model
    req_qual_score, matched_keywords = keyword_score(jd_req_qual_text, resume_full_text)
    resp_score = semantic_score(jd_resp_text, resume_work_text)
    pref_qual_score = semantic_score(jd_pref_qual_text, resume_full_text)
    skills_score = semantic_score(jd_skills_text, resume_skills_text)
    numeric_score, numeric_breakdown = numeric_metrics_score(resume_json)

    # 4. Combine scores using the defined weights
    weighted_total = (
        WEIGHTS["required_qualifications"] * req_qual_score +
        WEIGHTS["responsibilities"] * resp_score +
        WEIGHTS["preferred_qualifications"] * pref_qual_score +
        WEIGHTS["skills"] * skills_score +
        WEIGHTS["numeric_metrics"] * numeric_score
    )
    
    final_score_100 = round(weighted_total * 100, 2)

    return {
        "weights": WEIGHTS,
        "component_scores": {
            "required_qualifications_score": round(req_qual_score * 100, 2),
            "responsibilities_score": round(resp_score * 100, 2),
            "preferred_qualifications_score": round(pref_qual_score * 100, 2),
            "skills_score": round(skills_score * 100, 2),
            "numeric_metrics_score": round(numeric_score * 100, 2),
        },
        "numeric_metrics_breakdown": {k: round(v * 100, 2) for k, v in numeric_breakdown.items()},
        "matched_keywords_in_required_qualifications": matched_keywords,
        "final_ats_score": final_score_100,
        "score_scale": "0-100",
    }


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="ATS Scoring Engine (0-100)")
    parser.add_argument("--job", required=True, help="Path to job description JSON")
    parser.add_argument("--resume", required=True, help="Path to resume JSON")
    parser.add_argument("--output", default="ats_score.json", help="Output score JSON path")
    args = parser.parse_args()

    job_json = load_json(args.job)
    resume_json = load_json(args.resume)

    result = compute_ats_score(job_json, resume_json)
    save_json(args.output, result)

    print(json.dumps(result, indent=2))
    print(f"\nSaved ATS result to: {args.output}")


if __name__ == "__main__":
    main()
