import requests
import json

CODEFORCES_API = "https://codeforces.com/api"

def extract_codeforces_profile(username):
    """
    Extract Codeforces profile statistics and information
    """
    
    try:
        # Get user info
        user_info_url = f"{CODEFORCES_API}/user.info?handles={username}"
        user_response = requests.get(user_info_url)
        user_data = user_response.json()
        
        if user_data['status'] != 'OK':
            return {
                "error": "User not found",
                "username": username
            }
        
        user = user_data['result'][0]
        
        # Get user rating history
        rating_url = f"{CODEFORCES_API}/user.rating?handle={username}"
        rating_response = requests.get(rating_url)
        rating_data = rating_response.json()
        
        rating_history = []
        if rating_data['status'] == 'OK':
            rating_history = rating_data['result']
        
        # Get user submissions
        submissions_url = f"{CODEFORCES_API}/user.status?handle={username}&from=1&count=100"
        submissions_response = requests.get(submissions_url)
        submissions_data = submissions_response.json()
        
        submissions = []
        solved_problems = set()
        if submissions_data['status'] == 'OK':
            submissions = submissions_data['result']
            # Count unique solved problems
            for sub in submissions:
                if sub.get('verdict') == 'OK':
                    problem = sub['problem']
                    solved_problems.add(f"{problem['contestId']}{problem['index']}")
        
        # Count problems by rating
        rating_distribution = {}
        for sub in submissions:
            if sub.get('verdict') == 'OK' and 'rating' in sub['problem']:
                rating = sub['problem']['rating']
                rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        return {
            "profile_info": {
                "username": user.get('handle'),
                "first_name": user.get('firstName'),
                "last_name": user.get('lastName'),
                "country": user.get('country'),
                "city": user.get('city'),
                "organization": user.get('organization'),
                "rank": user.get('rank'),
                "max_rank": user.get('maxRank'),
                "rating": user.get('rating'),
                "max_rating": user.get('maxRating'),
                "friend_count": user.get('friendOfCount'),
                "contribution": user.get('contribution'),
                "registration_time": user.get('registrationTimeSeconds'),
                "profile_url": f"https://codeforces.com/profile/{username}"
            },
            "statistics": {
                "total_contests": len(rating_history),
                "problems_solved": len(solved_problems),
                "total_submissions": len(submissions),
                "rating_distribution": rating_distribution
            },
            "rating_history": rating_history[-10:] if rating_history else [],  # Last 10 contests
            "recent_submissions": [
                {
                    "problem": f"{s['problem']['contestId']}{s['problem']['index']} - {s['problem']['name']}",
                    "rating": s['problem'].get('rating'),
                    "verdict": s.get('verdict'),
                    "language": s.get('programmingLanguage'),
                    "time": s.get('creationTimeSeconds')
                }
                for s in submissions[:20]  # Last 20 submissions
            ]
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "username": username
        }

# -----------------------------
# MAIN DRIVER
# -----------------------------

if __name__ == "__main__":
    # Read from .env file
    with open('../.env', 'r') as f:
        lines = f.readlines()
        codeforces_username = None
        for line in lines:
            if 'codeforces' in line.lower():
                codeforces_username = line.split(':', 1)[1].strip()
                break
    
    if codeforces_username:
        print(f"Processing Codeforces profile: {codeforces_username}")
        
        profile_data = extract_codeforces_profile(codeforces_username)
        
        # Save to JSON file
        with open('codeforces_data.json', 'w') as f:
            json.dump(profile_data, f, indent=2)
        print("✓ Codeforces data saved to codeforces_data.json")
    else:
        print("Codeforces username not found in .env file")
