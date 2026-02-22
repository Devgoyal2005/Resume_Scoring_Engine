import requests
import base64
import re
import json
from urllib.parse import urlparse

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json"
    # Optional but recommended:
    # "Authorization": "Bearer YOUR_GITHUB_TOKEN"
}

# -----------------------------
# Utility Functions
# -----------------------------

def decode_readme(content):
    return base64.b64decode(content).decode("utf-8")

def extract_readme_metadata(readme_text):
    headings = re.findall(r"^#+\s+(.*)", readme_text, re.MULTILINE)
    links = re.findall(r"\[.*?\]\((.*?)\)", readme_text)
    images = re.findall(r"!\[.*?\]\((.*?)\)", readme_text)
    badges = [l for l in links if "shields.io" in l]

    tech_keywords = [
        "python", "java", "c++", "javascript", "react", "node",
        "fastapi", "django", "flask", "tensorflow", "pytorch",
        "docker", "kubernetes", "aws", "azure", "gcp", "solidity"
    ]

    detected_tech = [
        tech for tech in tech_keywords
        if re.search(rf"\b{re.escape(tech)}\b", readme_text, re.IGNORECASE)
    ]

    return {
        "headings": headings,
        "links": links,
        "images": images,
        "badges": badges,
        "detected_tech_stack": list(set(detected_tech))
    }

# -----------------------------
# PROFILE EXTRACTION
# -----------------------------

def extract_profile(username):
    profile_url = f"{GITHUB_API}/users/{username}"
    profile_repo_readme_url = f"{GITHUB_API}/repos/{username}/{username}/readme"

    profile = requests.get(profile_url, headers=HEADERS).json()

    readme_text = None
    readme_meta = {}

    readme_response = requests.get(profile_repo_readme_url, headers=HEADERS)

    if readme_response.status_code == 200:
        readme_json = readme_response.json()
        readme_text = decode_readme(readme_json["content"])
        readme_meta = extract_readme_metadata(readme_text)

    return {
        "profile_info": {
            "username": profile.get("login"),
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "followers": profile.get("followers"),
            "following": profile.get("following"),
            "public_repos": profile.get("public_repos"),
            "created_at": profile.get("created_at"),
            "profile_url": profile.get("html_url")
        },
        "profile_readme": {
            "exists": readme_text is not None,
            "content": readme_text,
            "metadata": readme_meta
        }
    }

# -----------------------------
# REPOSITORY EXTRACTION
# -----------------------------

def extract_repo(repo_url):
    path = urlparse(repo_url).path.strip("/").split("/")
    owner, repo = path[0], path[1]

    repo_api = f"{GITHUB_API}/repos/{owner}/{repo}"
    readme_api = f"{repo_api}/readme"
    languages_api = f"{repo_api}/languages"

    repo_data = requests.get(repo_api, headers=HEADERS).json()
    languages = requests.get(languages_api, headers=HEADERS).json()

    readme_text = None
    readme_meta = {}

    readme_response = requests.get(readme_api, headers=HEADERS)
    if readme_response.status_code == 200:
        readme_json = readme_response.json()
        readme_text = decode_readme(readme_json["content"])
        readme_meta = extract_readme_metadata(readme_text)

    return {
        "repo_info": {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "watchers": repo_data.get("watchers_count"),
            "topics": repo_data.get("topics"),
            "license": (repo_data.get("license") or {}).get("name"),
            "default_branch": repo_data.get("default_branch"),
            "open_issues": repo_data.get("open_issues_count"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "languages": languages,
            "repo_url": repo_data.get("html_url")
        },
        "repo_readme": {
            "exists": readme_text is not None,
            "content": readme_text,
            "metadata": readme_meta
        }
    }

# -----------------------------
# MAIN DRIVER
# -----------------------------

if __name__ == "__main__":
    # Read from .env file
    with open('../.env', 'r') as f:
        lines = f.readlines()
        username = None
        repo_url = None
        for line in lines:
            if 'github_profile' in line.lower():
                username = line.split(':', 1)[1].strip()
            elif 'github_repo' in line.lower():
                repo_url = line.split(':', 1)[1].strip()
    
    print(f"Processing GitHub username: {username}")
    print(f"Processing repo: {repo_url}")

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
