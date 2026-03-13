import requests
import base64
import re

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json"
    # Add a personal access token to raise rate limits:
    # "Authorization": "Bearer YOUR_GITHUB_TOKEN"
}

# Keywords scanned inside repo descriptions and READMEs to detect frameworks/tools
# beyond what the GitHub language API already reports.
FRAMEWORK_KEYWORDS = [
    # Web frameworks
    "react", "angular", "vue", "nextjs", "express", "nodejs", "django", "flask",
    "fastapi", "spring", "laravel", "rails", "nestjs", "svelte",
    # ML / Data Science
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "opencv", "hugging face", "transformers", "langchain",
    # Databases
    "mongodb", "postgresql", "mysql", "sqlite", "redis", "elasticsearch", "firebase",
    # DevOps / Cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible",
    "github actions", "jenkins", "ci/cd",
    # APIs / Protocols
    "graphql", "rest", "grpc", "websocket",
    # Other tooling
    "solidity", "web3", "kafka", "rabbitmq", "celery", "nginx", "linux",
]


def _detect_keywords(text):
    """Return any FRAMEWORK_KEYWORDS found in the given text (case-insensitive)."""
    text_lower = text.lower()
    return {
        kw for kw in FRAMEWORK_KEYWORDS
        if re.search(rf"\b{re.escape(kw)}\b", text_lower)
    }


import time

def _fetch_all_pages(url, params=None):
    """Fetch every page of a GitHub list endpoint and return the combined list."""
    results = []
    page = 1
    params = dict(params or {})
    params["per_page"] = 100
    while True:
        params["page"] = page
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", 0))
            wait  = max(reset - int(time.time()), 0) + 2
            print(f"  ⚠ GitHub rate limit hit — waiting {wait}s")
            time.sleep(wait)
            resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return results


def _get_repo_languages(username, repo_name):
    """
    Fetch language bytes for one repo.  Retries once on rate-limit.
    Returns a dict {language: bytes} or {} on failure.
    """
    url  = f"{GITHUB_API}/repos/{username}/{repo_name}/languages"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 403:
        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait  = max(reset - int(time.time()), 0) + 2
        print(f"  ⚠ Rate limit hit fetching {repo_name} — waiting {wait}s")
        time.sleep(wait)
        resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        # GitHub returns {"message": "..."} dict on API errors
        if isinstance(data, dict) and "message" not in data:
            return data
    return {}


# -----------------------------
# MAIN EXTRACTION ENTRY POINT
# -----------------------------

def extract_github_data(username):
    """
    Extract GitHub profile and aggregate the complete tech stack across
    ALL of the user's own (non-fork) repositories.

    Returns:
        profile_info  – basic identity fields
        tech_stack    – aggregated language bytes, ranked language list,
                        and extra frameworks/tools detected from repo
                        descriptions and topics
    """
    # --- Profile ---
    profile = requests.get(f"{GITHUB_API}/users/{username}", headers=HEADERS).json()

    # --- All owned (non-fork) repos ---
    all_repos = _fetch_all_pages(
        f"{GITHUB_API}/users/{username}/repos",
        params={"type": "owner"}
    )
    own_repos = [r for r in all_repos if not r.get("fork")]
    print(f"  → Scanning {len(own_repos)} repos for tech stack...")

    aggregated_languages = {}   # language → total bytes across all repos
    all_topics           = set()
    detected_tools       = set()

    for repo in own_repos:
        repo_name = repo["name"]

        # Language bytes for this repo
        repo_langs = _get_repo_languages(username, repo_name)
        for lang, byte_count in repo_langs.items():
            aggregated_languages[lang] = aggregated_languages.get(lang, 0) + byte_count

        # Topics (often framework/tool names)
        topics = repo.get("topics") or []
        all_topics.update(topics)

        # Scan description for additional framework/tool keywords
        detected_tools.update(_detect_keywords(repo.get("description") or ""))
        # Scan repo name as well (many repos are named after the tool they use)
        detected_tools.update(_detect_keywords(repo_name.replace("-", " ").replace("_", " ")))

    # Topics on GitHub are often tool names — fold them in
    detected_tools.update(all_topics)

    # Rank languages by total byte count (most-used first)
    languages_ranked = sorted(
        aggregated_languages, key=aggregated_languages.get, reverse=True
    )

    return {
        "profile_info": {
            "username":    profile.get("login"),
            "name":        profile.get("name"),
            "bio":         profile.get("bio"),
            "public_repos": profile.get("public_repos"),
            "followers":    profile.get("followers"),
            "profile_url":  profile.get("html_url"),
        },
        "tech_stack": {
            "languages":        aggregated_languages,
            "languages_ranked": languages_ranked,
            "topics_and_tools": sorted(detected_tools),
        },
    }


# -----------------------------
# MAIN DRIVER
# -----------------------------

if __name__ == "__main__":
    with open('../.env', 'r') as f:
        username = None
        for line in f:
            if line.lower().startswith('github_profile'):
                username = line.split(':', 1)[1].strip()
                break
    if username:
        import json
        data = extract_github_data(username)
        with open('github_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print("✓ GitHub data saved to github_data.json")

    profile_json = extract_profile(username)
    repo_json = extract_repo(repo_url)

    # Save profile JSON to file
    with open('profile_data.json', 'w') as f:
        json.dump(profile_json, f, indent=2)
    print("\n✓ Profile data saved to profile_data.json")

    # Save repo JSON to file
    with open('repo_data.json', 'w') as f:
        json.dump(repo_json, f, indent=2)
    print("✓ Repository data saved to repo_data.json")
