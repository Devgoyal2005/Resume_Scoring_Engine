import requests
import json
from bs4 import BeautifulSoup

CODECHEF_API = "https://www.codechef.com"

def extract_codechef_profile(username):
    """
    Extract CodeChef profile statistics and information
    Note: CodeChef doesn't have a public API, so we use web scraping
    This may break if CodeChef changes their HTML structure
    """
    
    try:
        profile_url = f"{CODECHEF_API}/users/{username}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code != 200:
            return {
                "error": "User not found or unable to fetch profile",
                "username": username
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a basic structure - actual scraping depends on CodeChef's HTML
        # You may need to inspect the page and update selectors
        
        profile_data = {
            "profile_info": {
                "username": username,
                "profile_url": profile_url,
                "name": None,
                "country": None,
                "current_rating": None,
                "highest_rating": None,
                "global_rank": None,
                "country_rank": None,
                "stars": None
            },
            "statistics": {
                "problems_solved": None,
                "total_contests": None,
                "div1_contests": 0,
                "div2_contests": 0,
                "div3_contests": 0
            },
            "recent_activity": [],
            "note": "CodeChef scraping requires HTML parsing - data may be incomplete"
        }
        
        # Try to extract rating (this is an example - actual selectors may differ)
        try:
            rating_div = soup.find('div', {'class': 'rating-number'})
            if rating_div:
                profile_data['profile_info']['current_rating'] = rating_div.text.strip()
        except:
            pass
        
        # Try to extract name
        try:
            name_header = soup.find('h1', {'class': 'h2-style'})
            if name_header:
                profile_data['profile_info']['name'] = name_header.text.strip()
        except:
            pass
        
        return profile_data
    
    except Exception as e:
        return {
            "error": str(e),
            "username": username,
            "note": "CodeChef requires web scraping - consider using alternative data sources"
        }

# -----------------------------
# MAIN DRIVER
# -----------------------------

if __name__ == "__main__":
    # Read from .env file
    with open('../.env', 'r') as f:
        lines = f.readlines()
        codechef_username = None
        for line in lines:
            if 'codechef' in line.lower():
                codechef_username = line.split(':', 1)[1].strip()
                break
    
    if codechef_username:
        print(f"Processing CodeChef profile: {codechef_username}")
        
        profile_data = extract_codechef_profile(codechef_username)
        
        # Save to JSON file
        with open('codechef_data.json', 'w') as f:
            json.dump(profile_data, f, indent=2)
        print("✓ CodeChef data saved to codechef_data.json")
        print("\nNote: CodeChef scraping may be limited due to lack of public API")
    else:
        print("CodeChef username not found in .env file")
