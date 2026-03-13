# Resume Scoring Engine

End-to-end pipeline that:
1. Reads base candidate data from `individual1.json`
2. Extracts platform usernames from JSON (no `.env` dependency)
3. Pulls data from GitHub, LeetCode, Codeforces, CodeChef
4. Merges all data into `resume.json`
5. Computes ATS score out of 100 using TF-IDF + cosine similarity

---

## Project Structure

```text
Resume_Scoring_Engine/
+-- individual1.json
+-- job_description.json
+-- resume.json
+-- ats_scoring_engine.py
+-- ats_score.json
+-- requirements.txt
+-- pipeline.py
+-- extraction/
    +-- __init__.py
    +-- extract_links.py
    +-- extract_all.py
    +-- merge_data.py
    +-- github/
    ¦   +-- git.py
    +-- leetcode/
    ¦   +-- leetcode.py
    +-- codeforces/
    ¦   +-- codeforces.py
    +-- codechef/
        +-- codechef.py
```

---

## Pipeline Flow

### Step 1: Extract links/usernames
`extraction/extract_links.py` reads `individual1.json` and extracts:
- `github_profile`
- `leetcode`
- `codeforces`
- `codechef`

### Step 2: Fetch platform data
`extraction/extract_all.py` fetches data per platform and writes:
- `extraction/github/github_data.json`
- `extraction/leetcode/leetcode_data.json`
- `extraction/codeforces/codeforces_data.json`
- `extraction/codechef/codechef_data.json`

### Step 3: Merge
`extraction/merge_data.py` merges extracted data into final `resume.json`.

Run complete pipeline:

```bash
python pipeline.py
```

---

## ATS Scoring Engine

Run ATS scorer:

```bash
python ats_scoring_engine.py --job job_description.json --resume resume.json --output ats_score.json
```

### ATS Weights

```python
WEIGHTS = {
    "exact_keyword": 0.35,
    "job_title": 0.25,
    "semantic_similarity": 0.20,
    "summary_similarity": 0.15,
    "numeric_metrics": 0.05,
}
```

### Scoring Method
- Text normalization (lowercase, cleanup, stopword removal, lemmatization when available)
- TF-IDF + cosine similarity (implemented in-script)
- Exact keyword overlap against important JD terms
- Title similarity
- Numeric coding profile metrics (LeetCode/GitHub/etc.)
- Final score reported on `0-100` scale

---

## Environment Setup

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Notes

- No notebook is required for the ATS engine.
- Username extraction is directly from `individual1.json`.
- Missing platforms are safely skipped.
- NLTK failures/corrupt cache are handled with fallback logic.
