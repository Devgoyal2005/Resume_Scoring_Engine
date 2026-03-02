import requests
import json
from bs4 import BeautifulSoup
import re

CODECHEF_API = "https://www.codechef.com"

def extract_codechef_profile(username):
    """
    Extract comprehensive CodeChef profile information using HTML scraping
    Scrapes all available information from the public profile page
    """
    
    try:
        profile_url = f"{CODECHEF_API}/users/{username}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.codechef.com/'
        }
        
        session = requests.Session()
        response = session.get(profile_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {
                "error": f"Unable to fetch profile - HTTP {response.status_code}",
                "username": username,
                "profile_url": profile_url
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize comprehensive profile data structure
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
                "stars": None,
                "student_professional": None,
                "institution": None,
                "teams": []
            },
            "statistics": {
                "problems_solved": {
                    "total": 0,
                    "fully_solved": 0,
                    "partially_solved": 0
                },
                "contest_stats": {
                    "total_contests": 0,
                    "contests_by_type": {}
                },
                "practice_problems": 0,
                "submissions": 0
            },
            "ratings": {
                "long_challenge": None,
                "cook_off": None,
                "lunch_time": None
            },
            "recent_contests": [],
            "badges": [],
            "problem_categories": {},
            "raw_html_available": True
        }
        
        # Extract full name (multiple possible locations)
        name_candidates = [
            soup.find('div', class_='user-details-container'),
            soup.find('h1', class_='h2-style'),
            soup.find('h2', class_='h2-style'),
            soup.find('div', class_='user-name')
        ]
        
        for candidate in name_candidates:
            if candidate and not profile_data['profile_info']['name']:
                name_text = candidate.get_text(strip=True)
                # Clean up the name (remove username if present)
                if name_text and name_text != username:
                    profile_data['profile_info']['name'] = name_text.replace(username, '').strip()
        
        # Extract current rating (try multiple selectors)
        rating_selectors = [
            ('div', 'rating-number'),
            ('div', 'rating'),
            ('span', 'rating-number')
        ]
        
        for tag, class_name in rating_selectors:
            rating_elem = soup.find(tag, class_=class_name)
            if rating_elem and not profile_data['profile_info']['current_rating']:
                try:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_num = int(re.search(r'\d+', rating_text).group())
                    profile_data['profile_info']['current_rating'] = rating_num
                    break
                except:
                    pass
        
        # Extract highest rating from text
        page_text = soup.get_text()
        highest_match = re.search(r'Highest\s+Rating[:\s]*(\d+)', page_text, re.IGNORECASE)
        if highest_match:
            profile_data['profile_info']['highest_rating'] = int(highest_match.group(1))
        
        # Extract stars
        star_matches = re.findall(r'(\d+)\s*[★\*]', page_text)
        if star_matches:
            profile_data['profile_info']['stars'] = f"{star_matches[0]}★"
        
        # Extract country
        country_selectors = [
            soup.find('span', class_='user-country-name'),
            soup.find('div', class_='country'),
            soup.find('span', class_='country-name')
        ]
        
        for selector in country_selectors:
            if selector and not profile_data['profile_info']['country']:
                profile_data['profile_info']['country'] = selector.get_text(strip=True)
        
        # Extract ranks from page text
        global_rank_match = re.search(r'Global\s+Rank[:\s]*(\d+)', page_text, re.IGNORECASE)
        if global_rank_match:
            profile_data['profile_info']['global_rank'] = int(global_rank_match.group(1))
        
        country_rank_match = re.search(r'Country\s+Rank[:\s]*(\d+)', page_text, re.IGNORECASE)
        if country_rank_match:
            profile_data['profile_info']['country_rank'] = int(country_rank_match.group(1))
        
        # Extract institution/organization
        institution_patterns = [
            r'Institution[:\s]*([^\n]+)',
            r'Organization[:\s]*([^\n]+)',
            r'Student[^:]*:[^\n]*at\s+([^\n]+)'
        ]
        
        for pattern in institution_patterns:
            inst_match = re.search(pattern, page_text, re.IGNORECASE)
            if inst_match and not profile_data['profile_info']['institution']:
                inst_text = inst_match.group(1).strip()
                if len(inst_text) > 2 and len(inst_text) < 100:
                    profile_data['profile_info']['institution'] = inst_text
        
        # Extract problems solved - try multiple methods
        fully_solved_patterns = [
            r'Fully\s+Solved[:\s]*(\d+)',
            r'Problems?\s+Solved[:\s]*(\d+)',
            r'Solved[:\s]*(\d+)\s+problems?'
        ]
        
        for pattern in fully_solved_patterns:
            solved_match = re.search(pattern, page_text, re.IGNORECASE)
            if solved_match:
                profile_data['statistics']['problems_solved']['fully_solved'] = int(solved_match.group(1))
                break
        
        # Try to find in sections
        problems_section = soup.find('section', class_='rating-data-section problems-solved')
        if problems_section:
            h5 = problems_section.find('h5')
            if h5:
                try:
                    num = int(re.search(r'\d+', h5.get_text()).group())
                    profile_data['statistics']['problems_solved']['fully_solved'] = max(
                        profile_data['statistics']['problems_solved']['fully_solved'], num
                    )
                except:
                    pass
        
        # Partially solved
        partial_match = re.search(r'Partially\s+Solved[:\s]*(\d+)', page_text, re.IGNORECASE)
        if partial_match:
            profile_data['statistics']['problems_solved']['partially_solved'] = int(partial_match.group(1))
        
        # Total problems
        profile_data['statistics']['problems_solved']['total'] = (
            profile_data['statistics']['problems_solved']['fully_solved'] + 
            profile_data['statistics']['problems_solved']['partially_solved']
        )
        
        # Extract contest participation
        contest_patterns = [
            r'Contests?\s+Participated[:\s]*(\d+)',
            r'(\d+)\s+Contests?\s+Participated',
            r'Total\s+Contests[:\s]*(\d+)'
        ]
        
        for pattern in contest_patterns:
            contest_match = re.search(pattern, page_text, re.IGNORECASE)
            if contest_match:
                profile_data['statistics']['contest_stats']['total_contests'] = int(contest_match.group(1))
                break
        
        # Try section method for contests
        contest_section = soup.find('section', class_='rating-data-section contest-participated-count')
        if contest_section:
            h5 = contest_section.find('h5')
            if h5:
                try:
                    num = int(re.search(r'\d+', h5.get_text()).group())
                    profile_data['statistics']['contest_stats']['total_contests'] = max(
                        profile_data['statistics']['contest_stats']['total_contests'], num
                    )
                except:
                    pass
        
        # Extract ratings by contest format
        rating_tables = soup.find_all('div', class_='rating-table')
        for table in rating_tables:
            table_text = table.get_text()
            
            # Extract contest type and rating
            if 'Long' in table_text or 'LONG' in table_text:
                rating_match = re.search(r'(\d+)', table_text)
                if rating_match:
                    profile_data['ratings']['long_challenge'] = int(rating_match.group(1))
            
            if 'Cook' in table_text or 'COOK' in table_text:
                rating_match = re.search(r'(\d+)', table_text)
                if rating_match:
                    profile_data['ratings']['cook_off'] = int(rating_match.group(1))
            
            if 'Lunch' in table_text or 'LTIME' in table_text:
                rating_match = re.search(r'(\d+)', table_text)
                if rating_match:
                    profile_data['ratings']['lunch_time'] = int(rating_match.group(1))
        
        # Extract recent contest performance
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:
                for row in rows[1:6]:  # Get up to 5 contests
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        contest_data = {}
                        for i, col in enumerate(cols):
                            text = col.get_text(strip=True)
                            if i == 0:
                                contest_data['contest'] = text
                            elif i == 1:
                                contest_data['rank'] = text
                            elif i == 2:
                                contest_data['problems_solved'] = text
                            elif i == 3:
                                contest_data['rating_change'] = text
                        
                        if contest_data and 'contest' in contest_data:
                            profile_data['recent_contests'].append(contest_data)
        
        # Extract badges/achievements
        badge_imgs = soup.find_all('img', src=re.compile(r'badge|achievement|award', re.IGNORECASE))
        for img in badge_imgs:
            badge = {
                'name': img.get('alt', img.get('title', 'Badge')),
                'image_url': img.get('src', '')
            }
            if badge['name'] and badge['name'] != 'Badge':
                profile_data['badges'].append(badge)
        
        # Extract all numeric stats from page for additional context
        all_numbers = re.findall(r'(\w+[^:]*?):\s*(\d+)', page_text)
        additional_stats = {}
        for key, value in all_numbers:
            key_clean = key.strip()
            if len(key_clean) < 50 and key_clean not in additional_stats:
                try:
                    additional_stats[key_clean] = int(value)
                except:
                    pass
        
        profile_data['additional_stats'] = additional_stats
        
        return profile_data
    
    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - CodeChef server took too long to respond",
            "username": username
        }
    except Exception as e:
        return {
            "error": str(e),
            "username": username,
            "error_type": type(e).__name__
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
        print("\nNote: CodeChef scraping extracts all visible public data")
    else:
        print("CodeChef username not found in .env file")
