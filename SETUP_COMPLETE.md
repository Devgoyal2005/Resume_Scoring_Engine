# Resume Scoring Engine - Pipeline Setup Complete! 🎉

## ✅ What Was Done

### 1. **Reorganized Project Structure**
   - Created `extraction/` folder containing all extraction modules
   - Moved the following into `extraction/`:
     - `codechef/` - CodeChef extraction module
     - `codeforces/` - Codeforces extraction module
     - `github/` - GitHub extraction module
     - `leetcode/` - LeetCode extraction module
     - `extract_all.py` - Multi-platform extraction script
     - `.env` - Configuration file

### 2. **Created New Pipeline Modules**
   - **`extraction/extract_links.py`**: Automatically extracts profile links from `individual1.json` and generates `.env` configuration
   - **`extraction/merge_data.py`**: Merges all extracted data with base resume info into final `resume.json`
   - **`pipeline.py`**: Main orchestrator that runs the entire process end-to-end

### 3. **Updated individual1.json**
   - Added actual competitive programming usernames:
     - LeetCode: NandiniAggarwal14
     - CodeChef: potato167
     - Codeforces: Benq

---

## 🚀 How to Use the Pipeline

### **Simple Usage (Recommended)**

Just run one command from the project root:

```bash
python pipeline.py
```

That's it! The pipeline will:
1. ✅ Read `individual1.json`
2. ✅ Extract all profile links
3. ✅ Fetch data from LeetCode, CodeChef, Codeforces, and GitHub
4. ✅ Merge everything into `resume.json`

### **Advanced Usage**

```bash
# Use custom input file
python pipeline.py --input myresume.json

# Specify custom output file
python pipeline.py --output final_resume.json

# Both custom input and output
python pipeline.py --input mydata.json --output result.json
```

### **View Help**

```bash
python pipeline.py --help
```

---

## 📁 New Project Structure

```
Resume_Scoring_Engine/
│
├── 📄 individual1.json          ← Your basic resume data
├── 📄 resume.json              ← Generated comprehensive resume
├── 🔧 pipeline.py              ← Main script to run
├── 📖 README_PIPELINE.md       ← Complete documentation
│
└── 📁 extraction/              ← All extraction code
    ├── extract_links.py
    ├── extract_all.py
    ├── merge_data.py
    ├── .env
    │
    ├── 📁 leetcode/
    ├── 📁 codechef/
    ├── 📁 codeforces/
    └── 📁 github/
```

---

## 🎯 Key Features

### ✅ **Fully Automated**
- One command to generate complete resume
- No manual configuration needed
- Automatically detects profile links from your JSON

### ✅ **Modular Design**
- Each step can be run independently
- Easy to extend with new platforms
- Clean separation of concerns

### ✅ **Smart Merging**
- Preserves all your original data
- Adds competitive programming statistics
- Includes GitHub profile and repository info

### ✅ **Error Handling**
- Gracefully handles missing profiles
- Continues even if one platform fails
- Clear error messages

---

## 📊 What Gets Extracted

### From LeetCode:
- Profile information (ranking, reputation)
- Problem statistics (Easy/Medium/Hard solved)
- Contest information
- Badges earned
- Recent submissions

### From CodeChef:
- Profile details (rating, rank, stars)
- Problem statistics
- Contest history
- Badges earned

### From Codeforces:
- Profile information (rating, rank)
- Contest statistics
- Rating history
- Recent submissions
- Problem-solving distribution

### From GitHub:
- Profile information (bio, followers, repos)
- Featured repository details
- Repository languages
- Repository description and README

---

## 🔄 Pipeline Flow

```
individual1.json
      ↓
  Extract Links
      ↓
   Generate .env
      ↓
 Fetch Platform Data
      ↓
  Merge Everything
      ↓
  resume.json
```

---

## 📝 Example Output

The generated `resume.json` will have this structure:

```json
{
  "personal_info": {
    "name": "Nandini Aggarwal",
    "links": {...},
    "competitive_programming_links": {...}
  },
  "projects": [...],        // Your projects
  "skills": {...},          // Your skills
  "experience": [...],      // Your experience
  "competitive_programming": {
    "leetcode": {...},      // Complete LeetCode stats
    "codechef": {...},      // Complete CodeChef stats
    "codeforces": {...}     // Complete Codeforces stats
  },
  "github": {...}           // GitHub profile & repo data
}
```

---

## 🛠️ Customization

### To add your own profile links:

Edit `individual1.json`:

```json
{
  "links": {
    "github": "https://github.com/YOUR_USERNAME",
    "linkedin": "https://linkedin.com/in/YOUR_PROFILE"
  },
  "competitive_programming_links": {
    "leetcode": "YOUR_LEETCODE_USERNAME",
    "codechef": "YOUR_CODECHEF_USERNAME",
    "codeforces": "YOUR_CODEFORCES_USERNAME"
  }
}
```

Then run:
```bash
python pipeline.py
```

---

## 🐛 Troubleshooting

### Issue: "Cannot find individual1.json"
**Solution**: Make sure you're running the command from the project root directory

### Issue: "No profile links found"
**Solution**: Add profile links to the `links` and `competitive_programming_links` sections in `individual1.json`

### Issue: Platform extraction failed
**Solution**: 
- Check your internet connection
- Verify the username exists on that platform
- The pipeline will continue even if one platform fails

---

## 📚 Additional Documentation

- **`README_PIPELINE.md`**: Complete detailed documentation
- **Individual module documentation**: See files in `extraction/` folder

---

## 🎓 Next Steps

1. **Update `individual1.json`** with your own information
2. **Run `python pipeline.py`** to generate your resume
3. **Use `resume.json`** as input for the ATS scoring engine

---

## 💡 Tips

- The pipeline caches data in `extraction/` folder - you can re-run merge without re-fetching if needed
- Add more projects to `individual1.json` to make your resume more comprehensive
- The featured GitHub repository is automatically selected from your first project

---

**Congratulations! Your resume extraction pipeline is ready to use! 🎉**

For questions or issues, refer to `README_PIPELINE.md` for complete documentation.
