# 🚀 Quick Reference Card

## One-Command Usage

```bash
python pipeline.py
```

That's it! ✨

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `individual1.json` | **INPUT** - Your base resume data |
| `resume.json` | **OUTPUT** - Complete generated resume |
| `pipeline.py` | **RUN THIS** - Main script |
| `run_pipeline.bat` | **WINDOWS** - Double-click to run |

---

## 📖 Documentation

| File | When to Read |
|------|--------------|
| `SETUP_COMPLETE.md` | **START HERE** - Quick guide |
| `README_PIPELINE.md` | **DETAILED** - Full documentation |
| `PROJECT_SUMMARY.md` | **OVERVIEW** - What was built |

---

## 🔧 Common Commands

```bash
# Basic run
python pipeline.py

# Custom input
python pipeline.py --input mydata.json

# Custom output
python pipeline.py --output final.json

# Help
python pipeline.py --help
```

---

## 📊 What You Get

**Input:** `individual1.json` (3 KB)
```json
{
  "projects": [...],
  "skills": {...},
  "links": {...},
  "competitive_programming_links": {...}
}
```

**Output:** `resume.json` (30 KB)
```json
{
  "personal_info": {...},
  "projects": [...],
  "skills": {...},
  "competitive_programming": {
    "leetcode": {...},
    "codechef": {...},
    "codeforces": {...}
  },
  "github": {...}
}
```

---

## ⚡ Pipeline Flow

```
individual1.json 
    ↓
Extract Links
    ↓
Fetch Data (LeetCode/CodeChef/Codeforces/GitHub)
    ↓
Merge Everything
    ↓
resume.json ✅
```

**Time:** 10-15 seconds

---

## ✅ Checklist

Before running:
- [ ] `individual1.json` exists
- [ ] Profile links added to JSON
- [ ] Internet connection active

After running:
- [ ] Check `resume.json` created
- [ ] Verify data looks correct
- [ ] Use for ATS scoring

---

## 🛠️ Troubleshooting

**Error:** "Cannot find individual1.json"
- **Fix:** Run from project root directory

**Error:** "No profile links found"  
- **Fix:** Add links to `individual1.json`

**Error:** Platform extraction failed
- **Fix:** Check username exists on that platform

---

## 📞 Need Help?

1. Read `SETUP_COMPLETE.md`
2. Check `README_PIPELINE.md`
3. Review error messages

---

## 🎯 Quick Tips

✅ Pipeline works with partial data (missing platforms OK)
✅ Can re-run anytime to refresh data
✅ Data cached in `extraction/` folder
✅ Safe to run multiple times

---

**Version:** 1.0.0 | **Status:** ✅ Ready to Use

*Keep this card handy for quick reference!* 📌
