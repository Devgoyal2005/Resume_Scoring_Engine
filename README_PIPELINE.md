# Resume Scoring Engine — Pipeline

A modular pipeline that reads `individual1.json`, fetches live data from GitHub,
LeetCode, Codeforces, and CodeChef, and writes a consolidated `resume.json` ready
for bias-free scoring.

---

## Folder Structure

```
Resume_Scoring_Engine/
├── individual1.json          # Input  — base resume (edit this; never auto-modified)
├── resume.json               # Output — merged result
├── pipeline.py               # Entry point: runs all three steps in order
│
└── extraction/
    ├── extract_links.py      # Step 1: reads individual1.json → writes .env
    ├── extract_all.py        # Step 2: calls each platform extractor → platform JSONs
    ├── merge_data.py         # Step 3: merges everything → resume.json
    ├── .env                  # Auto-generated; do not edit by hand
    │
    ├── github/
    │   ├── git.py            # Scans ALL repos, aggregates languages + topics
    │   └── github_data.json
    │
    ├── leetcode/
    │   ├── leetcode.py
    │   └── leetcode_data.json
    │
    ├── codeforces/
    │   ├── codeforces.py
    │   └── codeforces_data.json
    │
    └── codechef/
        ├── codechef.py
        └── codechef_data.json
```

---

## Input Format (`individual1.json`)

```json
{
  "name": "Your Name",
  "links": {
    "github":   "https://github.com/username",
    "linkedin": "https://linkedin.com/in/username"
  },
  "competitive_programming_links": {
    "leetcode":   "https://leetcode.com/username/",
    "codechef":   "https://www.codechef.com/users/username",
    "codeforces": "https://codeforces.com/profile/username"
  },
  "skills": { "languages": ["Python", "C++"] },
  "projects": [],
  "experience": []
}
```

Leave competitive-programming links as `""` if a platform is not used — the
pipeline will skip that extractor and still write an empty `{}` entry in
`resume.json` so all keys are always present.

---

## Usage

### Run the full pipeline (recommended)

```bash
python pipeline.py
```

Defaults: reads `individual1.json`, writes `resume.json`.

### Custom input / output paths

```bash
python pipeline.py --input path/to/resume_input.json --output path/to/result.json
```

### Run individual steps manually

```bash
# Step 1 — generate .env from individual1.json
cd extraction
python extract_links.py

# Step 2 — fetch platform data
python extract_all.py

# Step 3 — merge everything into resume.json
python merge_data.py
```

---

## Output Structure (`resume.json`)

```json
{
  "personal_info": {
    "name": "...",
    "links": { "github": "...", "linkedin": "..." },
    "competitive_programming_links": { "leetcode": "", "codechef": "", "codeforces": "" }
  },
  "projects":    [ ... ],
  "skills":      { ... },
  "experience":  [ ... ],
  "competitive_programming": {
    "leetcode":   { "username": "...", "problems_solved": {...}, "skill_tags": [...], "contest": {...} },
    "codechef":   { "username": "...", "current_rating": 0, "stars": "...", ... },
    "codeforces": { "username": "...", "rating": 0, "rank": "...", ... }
  },
  "github": {
    "profile_info": { "username": "...", "public_repos": 0, ... },
    "tech_stack": {
      "languages":         { "Python": 150000, ... },
      "languages_ranked":  ["Python", ...],
      "topics_and_tools":  ["flask", "docker", ...]
    },
    "repositories": [ { "name": "...", "languages": {...}, "topics": [...] } ]
  }
}
```

---

## What Each Extractor Captures

| Platform   | Fields extracted (skill-relevant only)                                                      |
|------------|----------------------------------------------------------------------------------------------|
| GitHub     | All non-fork repos · aggregated language bytes · repo topics · detected frameworks/tools    |
| LeetCode   | Problems solved (Easy/Medium/Hard) · skill tags · languages used · contest rating           |
| Codeforces | Rating / max rating · rank · contests attended · problems solved · rating distribution      |
| CodeChef   | Current & highest rating · stars · global rank · problems solved · total contests           |

**Excluded** (to avoid scoring bias): names, countries, institutions, submission lists,
badges, friend counts, recent-contest history.

---

## Dependencies

```bash
pip install requests beautifulsoup4 python-dotenv
```


## 📋 Overview

This pipeline takes a basic resume JSON file (`individual1.json`) as input, automatically extracts data from various coding platforms (LeetCode, CodeChef, Codeforces, GitHub), and generates a comprehensive `resume.json` with all combined information.

## 🏗️ Architecture

```
Resume_Scoring_Engine/
│
├── individual1.json          # Input: Basic resume data
├── resume.json              # Output: Complete resume with extracted data
├── pipeline.py              # Main orchestrator script
│
├── extraction/              # Extraction package
│   ├── __init__.py
│   ├── extract_links.py     # Extracts profile links from input JSON
│   ├── extract_all.py       # Fetches data from all platforms
│   ├── merge_data.py        # Merges all data into final resume
│   ├── .env                 # Auto-generated configuration
│   │
│   ├── leetcode/            # LeetCode extraction module
│   │   ├── leetcode.py
│   │   └── leetcode_data.json
│   │
│   ├── codechef/            # CodeChef extraction module
│   │   ├── codechef.py
│   │   └── codechef_data.json
│   │
│   ├── codeforces/          # Codeforces extraction module
│   │   ├── codeforces.py
│   │   └── codeforces_data.json
│   │
│   └── github/              # GitHub extraction module
│       ├── git.py
│       ├── profile_data.json
│       └── repo_data.json
```

## 🚀 Quick Start

### 1. Prepare Your Input File

Ensure your `individual1.json` has the following structure:

```json
{
  "projects": [...],
  "skills": {...},
  "experience": [...],
  "links": {
    "github": "https://github.com/username",
    "linkedin": "https://linkedin.com/in/username"
  },
  "competitive_programming_links": {
    "leetcode": "username or https://leetcode.com/username/",
    "codechef": "username or https://www.codechef.com/users/username",
    "codeforces": "username or https://codeforces.com/profile/username"
  }
}
```

### 2. Run the Pipeline

```bash
# Basic usage with default files
python pipeline.py

# With custom input/output files
python pipeline.py --input mydata.json --output final_resume.json

# Short form
python pipeline.py -i mydata.json -o output.json
```

### 3. Get Your Resume

The pipeline will automatically:
1. ✅ Extract profile links from your input JSON
2. ✅ Fetch data from LeetCode, CodeChef, Codeforces, and GitHub
3. ✅ Merge everything into a comprehensive `resume.json`

## 📊 Pipeline Workflow

```
┌─────────────────────┐
│  individual1.json   │
│  (Your basic info)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step 1: Extract    │
│  Profile Links      │ → Generates .env config
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step 2: Fetch      │
│  Platform Data      │ → Extracts from all platforms
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step 3: Merge      │
│  All Data           │ → Combines everything
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    resume.json      │
│ (Complete resume)   │
└─────────────────────┘
```

## 📦 Output Structure

The generated `resume.json` includes:

```json
{
  "personal_info": {
    "name": "...",
    "links": {...}
  },
  "projects": [...],
  "skills": {...},
  "experience": [...],
  "competitive_programming": {
    "leetcode": {
      "profile_info": {...},
      "problem_stats": {...},
      "contest_info": {...},
      "badges": [...],
      "recent_submissions": [...]
    },
    "codechef": {
      "profile_info": {...},
      "statistics": {...},
      "ratings": {...},
      "badges": [...]
    },
    "codeforces": {
      "profile_info": {...},
      "statistics": {...},
      "rating_history": [...],
      "recent_submissions": [...]
    }
  },
  "github": {
    "profile_info": {...},
    "featured_repository": {...}
  }
}
```

## 🔧 Manual Module Usage

You can also run individual modules separately if needed:

### Extract Links Only
```bash
cd extraction
python extract_links.py
```

### Fetch Platform Data Only
```bash
cd extraction
python extract_all.py
```

### Merge Data Only
```bash
cd extraction
python merge_data.py
```

## ⚙️ Configuration

The pipeline automatically generates a `.env` file in the `extraction/` folder based on your `individual1.json`. You can also manually edit it:

```
# GitHub
github_profile: username
github_repo: https://github.com/username/repo

# LeetCode
leetcode: username

# Codeforces
codeforces: username

# CodeChef
codechef: username
```

## 🐛 Troubleshooting

### No profile links found
- Ensure your `individual1.json` has `links` and `competitive_programming_links` sections
- Profile links should be valid URLs or usernames

### Extraction failed for a platform
- Check your internet connection
- Verify the username/profile exists on that platform
- Some platforms may have rate limits

### File not found errors
- Ensure you're running `pipeline.py` from the project root directory
- Check that `individual1.json` exists in the root directory

## 📝 Example

```bash
# 1. Edit your individual1.json with your information
# 2. Run the pipeline
python pipeline.py

# Output:
# ====================================================================
#                 RESUME GENERATION PIPELINE
# ====================================================================
#
# Input:  individual1.json
# Output: resume.json
# ====================================================================
#
# STEP 1: EXTRACTING PROFILE LINKS FROM INPUT FILE
# ✓ Configuration saved to extraction/.env
#   Found 5 profile(s)
#
# STEP 2: EXTRACTING DATA FROM PLATFORMS
# [1/4] Extracting GitHub data...
#   ✓ GitHub data saved successfully
# [2/4] Extracting LeetCode data...
#   ✓ LeetCode data saved successfully
# ...
#
# STEP 3: MERGING DATA INTO FINAL RESUME
# ✓ Final resume saved to resume.json
#
# ====================================================================
#                 ✓ PIPELINE COMPLETED SUCCESSFULLY!
# ====================================================================
```

## 🎯 Features

- ✅ **Fully Automated**: One command to generate complete resume
- ✅ **Modular Design**: Run individual steps independently if needed
- ✅ **Error Handling**: Graceful handling of missing data or failed extractions
- ✅ **Flexible Input**: Supports both URLs and plain usernames
- ✅ **Comprehensive Output**: Includes all platform statistics, ratings, and badges
- ✅ **Multiple Platforms**: LeetCode, CodeChef, Codeforces, and GitHub

## 📄 License

This project is part of the Resume Scoring Engine system.

## 🤝 Contributing

To add support for more platforms:
1. Create a new folder in `extraction/` (e.g., `hackerrank/`)
2. Implement extraction logic
3. Update `extract_all.py` to include the new platform
4. Update `merge_data.py` to merge the new data

---

**Happy Coding! 🚀**
