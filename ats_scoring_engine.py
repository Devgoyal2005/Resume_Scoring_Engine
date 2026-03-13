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
    NLTK_AVAILABLE = True
except ImportError:
    nltk = None  # type: ignore[assignment]
    stopwords = None  # type: ignore[assignment]
    WordNetLemmatizer = None  # type: ignore[assignment]
    NLTK_AVAILABLE = False

NLTK_READY = False


WEIGHTS = {
    "exact_keyword": 0.35,
    "job_title": 0.25,
    "semantic_similarity": 0.20,
    "summary_similarity": 0.15,
    "numeric_metrics": 0.05,
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


def _tf(tokens: List[str]) -> Dict[str, float]:
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = float(len(tokens))
    return {term: cnt / total for term, cnt in counts.items()}


def _idf(docs_tokens: List[List[str]]) -> Dict[str, float]:
    n_docs = len(docs_tokens)
    doc_freq: Counter = Counter()
    for tokens in docs_tokens:
        doc_freq.update(set(tokens))
    # Smoothed IDF
    return {term: math.log((1 + n_docs) / (1 + df)) + 1.0 for term, df in doc_freq.items()}


def _tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = _tf(tokens)
    return {term: tf_val * idf.get(term, 0.0) for term, tf_val in tf.items()}


def _cosine_dict(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(v1.get(k, 0.0) * v2.get(k, 0.0) for k in set(v1) | set(v2))
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return dot / (n1 * n2)


def cosine_score(text1: str, text2: str) -> float:
    """TF-IDF + cosine similarity without external ML dependency."""
    if not text1.strip() or not text2.strip():
        return 0.0

    tokens1 = text1.split()
    tokens2 = text2.split()
    idf = _idf([tokens1, tokens2])
    vec1 = _tfidf_vector(tokens1, idf)
    vec2 = _tfidf_vector(tokens2, idf)
    return _cosine_dict(vec1, vec2)


def exact_keyword_score(job_text: str, resume_text: str) -> Tuple[float, List[str]]:
    job_tokens = set(job_text.split())
    resume_tokens = set(resume_text.split())
    if not job_tokens:
        return 0.0, []

    matched = sorted(job_tokens.intersection(resume_tokens))
    return len(matched) / len(job_tokens), matched


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


def exact_keyword_score_critical(job_json: Dict[str, Any], resume_text: str) -> Tuple[float, List[str]]:
    job_keywords = set(extract_critical_keywords(job_json))
    resume_tokens = set(resume_text.split())
    if not job_keywords:
        return 0.0, []
    matched = sorted(job_keywords.intersection(resume_tokens))
    return len(matched) / len(job_keywords), matched


def job_title_score(job_title: str, resume_title: str) -> float:
    jt = normalize_text(job_title)
    rt = normalize_text(resume_title)
    if not jt or not rt:
        return 0.0
    if jt in rt or rt in jt:
        return 1.0
    cosine = cosine_score(jt, rt)
    jt_set = set(jt.split())
    rt_set = set(rt.split())
    jaccard = (len(jt_set & rt_set) / len(jt_set | rt_set)) if (jt_set or rt_set) else 0.0
    return max(cosine, jaccard)


def _safe_get(d: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def numeric_metrics_score(resume_json: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    # Pull numeric indicators (if available)
    leetcode_total = _safe_get(
        resume_json,
        ["competitive_programming", "leetcode", "problems_solved", "total"],
        0,
    )
    codeforces_rating = _safe_get(
        resume_json,
        ["competitive_programming", "codeforces", "profile_info", "rating"],
        0,
    )
    codechef_rating = _safe_get(
        resume_json,
        ["competitive_programming", "codechef", "profile_info", "current_rating"],
        0,
    )
    github_repos = _safe_get(resume_json, ["github", "profile_info", "public_repos"], 0)
    github_followers = _safe_get(resume_json, ["github", "profile_info", "followers"], 0)

    # Convert to normalized sub-scores [0,1]
    sub_scores = {
        "leetcode_problems": min(float(leetcode_total or 0) / 500.0, 1.0),
        "codeforces_rating": min(float(codeforces_rating or 0) / 2400.0, 1.0),
        "codechef_rating": min(float(codechef_rating or 0) / 2500.0, 1.0),
        "github_repos": min(float(github_repos or 0) / 30.0, 1.0),
        "github_followers": min(float(github_followers or 0) / 100.0, 1.0),
    }

    internal_weights = {
        "leetcode_problems": 0.35,
        "codeforces_rating": 0.20,
        "codechef_rating": 0.15,
        "github_repos": 0.20,
        "github_followers": 0.10,
    }

    # If values are missing/zero, keep score robust by using available non-zero signals
    active = [k for k, v in sub_scores.items() if v > 0]
    if not active:
        return 0.0, sub_scores

    active_weight_sum = sum(internal_weights[k] for k in active)
    score = sum(sub_scores[k] * internal_weights[k] for k in active) / active_weight_sum
    return score, sub_scores


def build_job_text(job_json: Dict[str, Any]) -> str:
    sections: List[str] = []
    sections.append(str(job_json.get("job_title", "")))
    sections.append(str(job_json.get("job_description", "")))
    sections.append(" ".join(job_json.get("responsibilities", []) or []))
    sections.append(" ".join(job_json.get("required_qualifications", []) or []))
    sections.append(" ".join(job_json.get("preferred_qualifications", []) or []))
    sections.append(" ".join(job_json.get("skills", []) or []))
    return " ".join(sections)


def build_resume_texts(resume_json: Dict[str, Any]) -> Tuple[str, str, str]:
    resume_title = str(
        resume_json.get("current_title")
        or _safe_get(resume_json, ["personal_info", "current_title"], "")
        or ""
    )

    projects_text = flatten_to_text(resume_json.get("projects", []))
    skills_text = flatten_to_text(resume_json.get("skills", {}))
    experience_text = flatten_to_text(resume_json.get("experience", []))
    github_bio = str(_safe_get(resume_json, ["github", "profile_info", "bio"], ""))

    # Experience-like corpus for semantic comparison with JD
    resume_experience_corpus = " ".join([projects_text, skills_text, experience_text])

    # Summary-like corpus for summary fit
    resume_summary_corpus = " ".join([github_bio, skills_text, projects_text])

    return resume_title, resume_experience_corpus, resume_summary_corpus


def compute_ats_score(job_json: Dict[str, Any], resume_json: Dict[str, Any]) -> Dict[str, Any]:
    job_title = str(job_json.get("job_title", ""))
    job_text_raw = build_job_text(job_json)

    resume_title_raw, resume_exp_raw, resume_summary_raw = build_resume_texts(resume_json)

    job_text = normalize_text(job_text_raw)
    resume_exp = normalize_text(resume_exp_raw)
    resume_summary = normalize_text(resume_summary_raw)

    exact_score, matched_keywords = exact_keyword_score_critical(job_json, resume_exp)

    # Title match fallback: if explicit title is missing in resume JSON,
    # compare job title against broader profile text to avoid hard 0.
    direct_title_score = job_title_score(job_title, resume_title_raw)
    inferred_title_score = job_title_score(job_title, resume_summary_raw)
    title_score = max(direct_title_score, inferred_title_score)
    semantic_sim = cosine_score(job_text, resume_exp)
    summary_sim = cosine_score(job_text, resume_summary)
    numeric_score, numeric_breakdown = numeric_metrics_score(resume_json)

    weighted_0_to_1 = (
        WEIGHTS["exact_keyword"] * exact_score
        + WEIGHTS["job_title"] * title_score
        + WEIGHTS["semantic_similarity"] * semantic_sim
        + WEIGHTS["summary_similarity"] * summary_sim
        + WEIGHTS["numeric_metrics"] * numeric_score
    )

    final_score_100 = round(weighted_0_to_1 * 100, 2)

    return {
        "weights": WEIGHTS,
        "component_scores": {
            "exact_keyword_score": round(exact_score * 100, 2),
            "job_title_score": round(title_score * 100, 2),
            "semantic_similarity": round(semantic_sim * 100, 2),
            "summary_similarity": round(summary_sim * 100, 2),
            "numeric_metrics": round(numeric_score * 100, 2),
        },
        "numeric_metrics_breakdown": {k: round(v * 100, 2) for k, v in numeric_breakdown.items()},
        "matched_keywords_count": len(matched_keywords),
        "matched_keywords_sample": matched_keywords[:40],
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
