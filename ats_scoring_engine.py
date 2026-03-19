import argparse
import json
import re
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

GENERIC_JOB_TERMS = {
    "looking", "engineer", "engineering", "software", "development", "developer",
    "experience", "required", "qualification", "preferred", "responsibility",
    "strong", "good", "knowledge", "understanding", "work", "working", "build",
    "team", "product", "customer", "system", "service", "services", "code",
    "clean", "maintainable", "scalable", "design", "develop", "year", "years",
}


def _ensure_nltk_resources() -> None:
    if not NLTK_AVAILABLE or nltk is None:
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
                return
        except Exception:
            return


_ensure_nltk_resources()
if NLTK_AVAILABLE and stopwords is not None and WordNetLemmatizer is not None:
    try:
        STOP_WORDS = set(stopwords.words("english"))
        LEMMATIZER = WordNetLemmatizer()
        NLTK_READY = True
    except Exception:
        STOP_WORDS = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "were", "will", "with", "or", "this", "these", "those",
        }
        LEMMATIZER = None
        NLTK_READY = False
else:
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "were", "will", "with", "or", "this", "these", "those",
    }
    LEMMATIZER = None
    NLTK_READY = False


# --- SCORING PROFILES ---

# Profile A: Emphasizes exact keyword matches.
# Use for sections where specific terminology is critical (e.g., Required Qualifications).
KEYWORD_BIASED_PROFILE = {
    "exact_keyword": 0.75,
    "semantic": 0.10,
    "numeric": 0.10,
    "job_title": 0.05,
}

# Profile B: Emphasizes contextual understanding.
# Use for sections where concepts are more important than keywords (e.g., Responsibilities).
SEMANTIC_BIASED_PROFILE = {
    "semantic": 0.75,
    "exact_keyword": 0.10,
    "numeric": 0.10,
    "job_title": 0.05,
}

# --- FINAL SCORE WEIGHTS ---
# Defines the importance of each job description section in the final score.
FINAL_SCORE_WEIGHTS = {
    "required_qualifications": 0.30,
    "responsibilities": 0.30,
    "preferred_qualifications": 0.20,
    "skills": 0.20,
}


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


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    tokens = text.split()
    if NLTK_READY:
        tokens = [w for w in tokens if w not in STOP_WORDS]
        if LEMMATIZER is not None:
            try:
                tokens = [LEMMATIZER.lemmatize(w) for w in tokens]
            except Exception:
                pass
    return " ".join(tokens)


def prepare_text_for_semantic(text: str) -> str:
    """A gentle text cleaner for the sentence-transformer model."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def job_title_score(job_title: str, resume_title: str) -> float:
    """Scores the match between the job title and resume title."""
    if not job_title or not resume_title:
        return 0.0
    
    job_norm = normalize_text(job_title)
    resume_norm = normalize_text(resume_title)

    if job_norm == resume_norm:
        return 1.0
    
    # Give partial credit for overlapping words
    job_tokens = set(job_norm.split())
    resume_tokens = set(resume_norm.split())
    
    if not job_tokens:
        return 0.0
        
    intersection = job_tokens.intersection(resume_tokens)
    return len(intersection) / len(job_tokens)


def numeric_metrics_score(job_section_text: str, resume_full_text: str) -> Tuple[float, Dict[str, Any]]:
    """Extracts and compares numeric values like years of experience."""
    # Simple regex to find numbers, optionally followed by '+'
    job_numbers = re.findall(r'(\d+)\+?', job_section_text)
    resume_numbers = re.findall(r'(\d+)\+?', resume_full_text)

    job_reqs = [int(n) for n in job_numbers]
    resume_stats = [int(n) for n in resume_numbers]

    if not job_reqs:
        return 0.0, {"message": "No numeric requirements found in job description section."}

    # Find the highest numeric value in the resume (e.g., for "5+ years")
    max_resume_stat = max(resume_stats) if resume_stats else 0
    
    # Check if the resume's max value meets each requirement
    met_requirements = sum(1 for req in job_reqs if max_resume_stat >= req)
    
    score = met_requirements / len(job_reqs)
    
    return score, {"job_requirements": job_reqs, "resume_values": resume_stats, "max_resume_value": max_resume_stat}


def semantic_score(text1: str, text2: str) -> float:
    """Computes semantic similarity using a sentence-transformer model."""
    clean_text1 = prepare_text_for_semantic(text1)
    clean_text2 = prepare_text_for_semantic(text2)

    if not clean_text1 or not clean_text2 or MODEL is None or util is None:
        return 0.0

    embedding1 = MODEL.encode(clean_text1, convert_to_tensor=True)
    embedding2 = MODEL.encode(clean_text2, convert_to_tensor=True)
    
    # Compute cosine-similarity
    cosine_scores = util.cos_sim(embedding1, embedding2)
    return cosine_scores.item()


def keyword_score(job_section_text: str, resume_full_text: str) -> Tuple[float, List[str]]:
    """Calculates exact keyword match score after proper normalization."""
    job_tokens = set(normalize_text(job_section_text).split())
    job_keywords = {token for token in job_tokens if token not in GENERIC_JOB_TERMS}
    resume_tokens = set(normalize_text(resume_full_text).split())

    if not job_keywords:
        return 0.0, []

    matched = sorted(list(job_keywords.intersection(resume_tokens)))
    score = len(matched) / len(job_keywords)
    return score, matched


def redistribute_weights_for_zeros(
    base_weights: Dict[str, float],
    scores: Dict[str, float],
    redistribution_ratio: float = 0.80,
) -> Tuple[Dict[str, float], float, List[str]]:
    """
    Redistribute weight from zero-score items to non-zero items.
    - `redistribution_ratio` portion is redistributed.
    - Remaining portion is treated as penalty (lost weight).
    Returns: (effective_weights, penalty_weight, zero_keys)
    """
    zero_keys = [k for k, v in scores.items() if v <= 0.0 and base_weights.get(k, 0.0) > 0.0]
    if not zero_keys:
        return dict(base_weights), 0.0, []

    non_zero_keys = [k for k, v in scores.items() if v > 0.0 and base_weights.get(k, 0.0) > 0.0]
    if not non_zero_keys:
        # Nothing to redistribute to; keep original and full penalty logic cannot be applied usefully.
        return dict(base_weights), 0.0, zero_keys

    total_zero_weight = sum(base_weights[k] for k in zero_keys)
    penalty_weight = total_zero_weight * (1.0 - redistribution_ratio)
    redistributed_weight = total_zero_weight * redistribution_ratio

    effective_weights = dict(base_weights)
    for k in zero_keys:
        effective_weights[k] = 0.0

    non_zero_base_sum = sum(base_weights[k] for k in non_zero_keys)
    if non_zero_base_sum > 0:
        for k in non_zero_keys:
            share = base_weights[k] / non_zero_base_sum
            effective_weights[k] += redistributed_weight * share

    return effective_weights, penalty_weight, zero_keys


def score_qualifications_smart(job_section_text: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based parser for education-focused qualification checks."""
    education = resume_data.get("education", {}) if isinstance(resume_data, dict) else {}
    if not isinstance(education, dict):
        education = {}

    applicable_checks = 0
    passed_count = 0
    passed_checks: List[str] = []
    check_details: Dict[str, Any] = {}

    # --- GPA Check ---
    gpa_match = re.search(
        r"minimum\s+gpa\s+of\s+(\d+\.?\d*)\s*/\s*(\d+\.?\d*)",
        job_section_text,
        flags=re.IGNORECASE,
    )
    candidate_gpa = education.get("current_gpa")
    candidate_scale = education.get("scale", 10.0)

    gpa_passed = False
    if gpa_match and candidate_gpa is not None:
        applicable_checks += 1
        required_gpa = float(gpa_match.group(1))
        required_scale = float(gpa_match.group(2))
        try:
            candidate_gpa_float = float(candidate_gpa)
            candidate_scale_float = float(candidate_scale) if candidate_scale is not None else 10.0
            if required_scale > 0 and candidate_scale_float > 0:
                required_on_candidate_scale = required_gpa * (candidate_scale_float / required_scale)
                gpa_passed = candidate_gpa_float >= required_on_candidate_scale
                check_details["gpa_check"] = {
                    "required": {"value": required_gpa, "scale": required_scale},
                    "candidate": {"value": candidate_gpa_float, "scale": candidate_scale_float},
                    "required_on_candidate_scale": round(required_on_candidate_scale, 2),
                    "passed": gpa_passed,
                }
        except (TypeError, ValueError):
            check_details["gpa_check"] = {"passed": False, "reason": "Invalid GPA format in resume."}
    else:
        check_details["gpa_check"] = {
            "passed": False,
            "applicable": False,
            "reason": "Could not find GPA rule in JD or GPA in resume education.",
        }

    if gpa_passed:
        passed_count += 1
        passed_checks.append("GPA check passed")

    # --- Graduation Year Check ---
    year_match = re.search(
        r"graduation\s+in\s+(\d{4})\s+or\s+before",
        job_section_text,
        flags=re.IGNORECASE,
    )
    candidate_grad_year = education.get("expected_graduation_year")

    year_passed = False
    if year_match and candidate_grad_year is not None:
        applicable_checks += 1
        required_latest_year = int(year_match.group(1))
        try:
            candidate_year_int = int(candidate_grad_year)
            year_passed = candidate_year_int <= required_latest_year
            check_details["graduation_year_check"] = {
                "required_latest_year": required_latest_year,
                "candidate_year": candidate_year_int,
                "passed": year_passed,
            }
        except (TypeError, ValueError):
            check_details["graduation_year_check"] = {
                "passed": False,
                "reason": "Invalid graduation year format in resume.",
            }
    else:
        check_details["graduation_year_check"] = {
            "passed": False,
            "applicable": False,
            "reason": "Could not find graduation year rule in JD or graduation year in resume education.",
        }

    if year_passed:
        passed_count += 1
        passed_checks.append("Graduation year check passed")

    # --- Degree Title Check ---
    required_degree_keywords: List[str] = []
    if re.search(r"\bb\.?\s?tech\b", job_section_text, flags=re.IGNORECASE):
        required_degree_keywords.append("b.tech")
    if re.search(r"computer\s+science", job_section_text, flags=re.IGNORECASE):
        required_degree_keywords.append("computer science")

    candidate_degree = str(education.get("degree", "") or "")
    candidate_degree_norm = re.sub(r"\s+", " ", candidate_degree.lower()).strip()

    degree_passed = False
    if required_degree_keywords and candidate_degree_norm:
        applicable_checks += 1
        normalized_required = [k.replace(".", "") for k in required_degree_keywords]
        normalized_candidate = candidate_degree_norm.replace(".", "")
        degree_passed = all(k in normalized_candidate for k in normalized_required)
        check_details["degree_title_check"] = {
            "required_keywords": required_degree_keywords,
            "candidate_degree": candidate_degree,
            "passed": degree_passed,
        }
    else:
        check_details["degree_title_check"] = {
            "required_keywords": required_degree_keywords,
            "candidate_degree": candidate_degree,
            "passed": False,
            "reason": "Missing JD degree keywords or candidate degree.",
        }

    if degree_passed:
        passed_count += 1
        passed_checks.append("Degree title check passed")

    final_score = (passed_count / applicable_checks) * 100.0 if applicable_checks > 0 else 0.0

    return {
        "score": round(min(final_score, 100.0), 2),
        "details": passed_checks,
        "applicable_checks": applicable_checks,
        "passed_checks_count": passed_count,
        "checks": check_details,
    }


def compute_ats_score(job_json: Dict[str, Any], resume_json: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Extract and prepare text from resume
    resume_full_text = flatten_to_text(resume_json)
    resume_title = resume_json.get("current_title", "")

    # 2. Extract text and title from job description
    job_title = job_json.get("job_title") or job_json.get("title", "")
    jd_sections = {
        "required_qualifications": flatten_to_text(job_json.get("required_qualifications", [])),
        "responsibilities": flatten_to_text(job_json.get("responsibilities", [])),
        "preferred_qualifications": flatten_to_text(job_json.get("preferred_qualifications", [])),
        "skills": flatten_to_text(job_json.get("skills", [])),
    }

    # 3. Calculate scores for each section using the Profile-Based system
    component_scores = {}
    section_score_values: Dict[str, float] = {}
    section_penalties: Dict[str, float] = {}
    
    # --- Required Qualifications (Keyword Biased) ---
    req_qual_text = jd_sections["required_qualifications"]
    education_data = resume_json.get("education", {}) if isinstance(resume_json, dict) else {}
    if req_qual_text.strip() and isinstance(education_data, dict) and education_data:
        smart_result = score_qualifications_smart(req_qual_text, resume_json)
        req_qual_final_score = smart_result["score"] / 100.0

        section_score_values["required_qualifications"] = req_qual_final_score
        section_penalties["required_qualifications"] = 0.0

        component_scores["required_qualifications"] = {
            "profile_used": "Smart-Parser",
            "final_section_score": round(smart_result["score"], 2),
            "breakdown": {
                "smart_parser_score": round(smart_result["score"], 2),
            },
            "effective_component_weights": {"smart_parser": 1.0},
            "zero_components": [] if smart_result["score"] > 0.0 else ["smart_parser"],
            "penalty_weight_due_to_zeros": 0.0,
            "matched_details": smart_result["details"],
            "smart_parser_details": smart_result["checks"],
        }
    else:
        kw_score, matched_kws = keyword_score(req_qual_text, resume_full_text)
        sem_score = semantic_score(req_qual_text, resume_full_text)
        num_score, num_breakdown = numeric_metrics_score(req_qual_text, resume_full_text)
        jt_score = job_title_score(job_title, resume_title)

        req_raw_scores = {
            "exact_keyword": kw_score,
            "semantic": sem_score,
            "numeric": num_score,
            "job_title": jt_score,
        }
        req_effective_weights, req_penalty_weight, req_zero_components = redistribute_weights_for_zeros(
            KEYWORD_BIASED_PROFILE,
            req_raw_scores,
            redistribution_ratio=0.80,
        )

        req_qual_final_score = (
            req_raw_scores["exact_keyword"] * req_effective_weights["exact_keyword"] +
            req_raw_scores["semantic"] * req_effective_weights["semantic"] +
            req_raw_scores["numeric"] * req_effective_weights["numeric"] +
            req_raw_scores["job_title"] * req_effective_weights["job_title"]
        )
        section_score_values["required_qualifications"] = req_qual_final_score
        section_penalties["required_qualifications"] = req_penalty_weight

        component_scores["required_qualifications"] = {
            "profile_used": "Keyword-Biased",
            "final_section_score": round(req_qual_final_score * 100, 2),
            "breakdown": {
                "exact_keyword_score": round(kw_score * 100, 2),
                "semantic_similarity": round(sem_score * 100, 2),
                "numeric_metrics_score": round(num_score * 100, 2),
                "job_title_score": round(jt_score * 100, 2),
            },
            "effective_component_weights": req_effective_weights,
            "zero_components": req_zero_components,
            "penalty_weight_due_to_zeros": round(req_penalty_weight, 4),
            "matched_keywords": matched_kws,
            "numeric_details": num_breakdown,
        }

    # --- Responsibilities, Preferred Quals, Skills (Semantic Biased) ---
    for section_name in ["responsibilities", "preferred_qualifications", "skills"]:
        section_text = jd_sections[section_name]
        if not section_text.strip():
            section_score_values[section_name] = 0.0
            section_penalties[section_name] = 0.0
            component_scores[section_name] = {
                "profile_used": "Semantic-Biased",
                "final_section_score": 0.0,
                "breakdown": {
                    "semantic_similarity": 0.0,
                    "exact_keyword_score": 0.0,
                    "numeric_metrics_score": 0.0,
                    "job_title_score": 0.0,
                },
                "effective_component_weights": SEMANTIC_BIASED_PROFILE,
                "zero_components": ["semantic", "exact_keyword", "numeric", "job_title"],
                "penalty_weight_due_to_zeros": 0.0,
                "missing_in_job_description": True,
            }
            continue

        kw_score, _ = keyword_score(section_text, resume_full_text)
        sem_score = semantic_score(section_text, resume_full_text)
        num_score, num_breakdown = numeric_metrics_score(section_text, resume_full_text)
        jt_score = job_title_score(job_title, resume_title)

        raw_scores = {
            "exact_keyword": kw_score,
            "semantic": sem_score,
            "numeric": num_score,
            "job_title": jt_score,
        }
        effective_weights, penalty_weight, zero_components = redistribute_weights_for_zeros(
            SEMANTIC_BIASED_PROFILE,
            raw_scores,
            redistribution_ratio=0.80,
        )

        final_section_score = (
            sem_score * effective_weights["semantic"] +
            kw_score * effective_weights["exact_keyword"] +
            num_score * effective_weights["numeric"] +
            jt_score * effective_weights["job_title"]
        )
        section_score_values[section_name] = final_section_score
        section_penalties[section_name] = penalty_weight

        component_scores[section_name] = {
            "profile_used": "Semantic-Biased",
            "final_section_score": round(final_section_score * 100, 2),
            "breakdown": {
                "semantic_similarity": round(sem_score * 100, 2),
                "exact_keyword_score": round(kw_score * 100, 2),
                "numeric_metrics_score": round(num_score * 100, 2),
                "job_title_score": round(jt_score * 100, 2),
            },
            "effective_component_weights": effective_weights,
            "zero_components": zero_components,
            "penalty_weight_due_to_zeros": round(penalty_weight, 4),
            "numeric_details": num_breakdown,
        }

    # 4. Redistribute top-level section weights if any section score is zero.
    effective_final_weights, final_weight_penalty, zero_sections = redistribute_weights_for_zeros(
        FINAL_SCORE_WEIGHTS,
        section_score_values,
        redistribution_ratio=0.80,
    )

    # 5. Calculate the final weighted ATS score
    weighted_total = (
        section_score_values["required_qualifications"] * effective_final_weights["required_qualifications"] +
        section_score_values["responsibilities"] * effective_final_weights["responsibilities"] +
        section_score_values["preferred_qualifications"] * effective_final_weights["preferred_qualifications"] +
        section_score_values["skills"] * effective_final_weights["skills"]
    )
    
    final_score_100 = round(weighted_total * 100, 2)

    return {
        "final_ats_score": final_score_100,
        "score_scale": "0-100",
        "scoring_profiles": {
            "keyword_biased": KEYWORD_BIASED_PROFILE,
            "semantic_biased": SEMANTIC_BIASED_PROFILE,
        },
        "final_score_weights": FINAL_SCORE_WEIGHTS,
        "effective_final_score_weights": effective_final_weights,
        "zero_score_sections": zero_sections,
        "final_weight_penalty_due_to_zero_sections": round(final_weight_penalty, 4),
        "component_scores": component_scores,
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
