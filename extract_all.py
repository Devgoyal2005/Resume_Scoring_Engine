import json
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(__file__))

from github.git import extract_profile as extract_github_profile, extract_repo as extract_github_repo
from leetcode.leetcode import extract_leetcode_profile
from codeforces.codeforces import extract_codeforces_profile
from codechef.codechef import extract_codechef_profile

def load_env_config():
    """Load configuration from .env file"""
    config = {}
    
    with open('.env', 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
    
    return config

def extract_all_profiles():
    """Extract data from all platforms and save to respective folders"""
    
    print("=" * 60)
    print("PROFILE DATA EXTRACTION - CODING PLATFORMS")
    print("=" * 60)
    
    # Load configuration
    config = load_env_config()
    
    # GitHub Extraction
    if config.get('github_profile') and config.get('github_repo'):
        print("\n[1/4] Extracting GitHub data...")
        try:
            username = config['github_profile']
            repo_url = config['github_repo']
            
            print(f"  → Profile: {username}")
            print(f"  → Repo: {repo_url}")
            
            profile_data = extract_github_profile(username)
            repo_data = extract_github_repo(repo_url)
            
            # Save to github folder
            with open('github/profile_data.json', 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            with open('github/repo_data.json', 'w') as f:
                json.dump(repo_data, f, indent=2)
            
            print("  ✓ GitHub data saved successfully")
        except Exception as e:
            print(f"  ✗ GitHub extraction failed: {str(e)}")
    else:
        print("\n[1/5] Skipping GitHub - credentials not found in .env")
    
    # LeetCode Extraction
    if config.get('leetcode'):
        print("\n[2/4] Extracting LeetCode data...")
        try:
            username = config['leetcode']
            print(f"  → Username: {username}")
            
            leetcode_data = extract_leetcode_profile(username)
            
            # Save to leetcode folder
            with open('leetcode/leetcode_data.json', 'w') as f:
                json.dump(leetcode_data, f, indent=2)
            
            print("  ✓ LeetCode data saved successfully")
        except Exception as e:
            print(f"  ✗ LeetCode extraction failed: {str(e)}")
    else:
        print("\n[2/5] Skipping LeetCode - username not found in .env")
    
    # Codeforces Extraction
    if config.get('codeforces'):
        print("\n[3/4] Extracting Codeforces data...")
        try:
            username = config['codeforces']
            print(f"  → Username: {username}")
            
            codeforces_data = extract_codeforces_profile(username)
            
            # Save to codeforces folder
            with open('codeforces/codeforces_data.json', 'w') as f:
                json.dump(codeforces_data, f, indent=2)
            
            print("  ✓ Codeforces data saved successfully")
        except Exception as e:
            print(f"  ✗ Codeforces extraction failed: {str(e)}")
    else:
        print("\n[3/5] Skipping Codeforces - username not found in .env")
    
    # CodeChef Extraction
    if config.get('codechef'):
        print("\n[4/4] Extracting CodeChef data...")
        try:
            username = config['codechef']
            print(f"  → Username: {username}")
            
            codechef_data = extract_codechef_profile(username)
            
            # Save to codechef folder
            with open('codechef/codechef_data.json', 'w') as f:
                json.dump(codechef_data, f, indent=2)
            
            print("  ✓ CodeChef data saved successfully")
        except Exception as e:
            print(f"  ✗ CodeChef extraction failed: {str(e)}")
    else:
        print("\n[4/4] Skipping CodeChef - username not found in .env")
    
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE!")
    print("=" * 60)
    print("\nData saved in respective folders:")
    print("  • github/profile_data.json & github/repo_data.json")
    print("  • leetcode/leetcode_data.json")
    print("  • codeforces/codeforces_data.json")
    print("  • codechef/codechef_data.json")
    print("=" * 60)

if __name__ == "__main__":
    extract_all_profiles()
