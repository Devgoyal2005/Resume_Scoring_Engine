import requests
import json

LEETCODE_API = "https://leetcode.com/graphql"

def extract_leetcode_profile(username):
    """
    Extract LeetCode profile statistics and information
    """
    
    # GraphQL query for user profile
    query = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
                ranking
                reputation
                websites
                countryName
                skillTags
                realName
                aboutMe
            }
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                }
                totalSubmissionNum {
                    difficulty
                    count
                }
            }
            badges {
                name
                icon
            }
        }
        userContestRanking(username: $username) {
            attendedContestsCount
            rating
            globalRanking
            topPercentage
        }
        recentSubmissionList(username: $username) {
            title
            titleSlug
            timestamp
            statusDisplay
            lang
        }
    }
    """
    
    variables = {"username": username}
    
    try:
        response = requests.post(
            LEETCODE_API,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )
        
        data = response.json()
        
        if not data.get('data') or not data['data'].get('matchedUser'):
            return {
                "error": "User not found or API error",
                "username": username
            }
        
        user = data['data']['matchedUser']
        contest = data['data'].get('userContestRanking', {})
        submissions = data['data'].get('recentSubmissionList', [])
        
        # Parse submission stats
        ac_stats = {item['difficulty']: item['count'] for item in user['submitStats']['acSubmissionNum']}
        total_stats = {item['difficulty']: item['count'] for item in user['submitStats']['totalSubmissionNum']}
        
        return {
            "profile_info": {
                "username": user['username'],
                "real_name": user['profile'].get('realName'),
                "ranking": user['profile'].get('ranking'),
                "reputation": user['profile'].get('reputation'),
                "country": user['profile'].get('countryName'),
                "about": user['profile'].get('aboutMe'),
                "websites": user['profile'].get('websites', []),
                "skill_tags": user['profile'].get('skillTags', [])
            },
            "problem_stats": {
                "accepted": {
                    "All": ac_stats.get('All', 0),
                    "Easy": ac_stats.get('Easy', 0),
                    "Medium": ac_stats.get('Medium', 0),
                    "Hard": ac_stats.get('Hard', 0)
                },
                "total_submissions": {
                    "All": total_stats.get('All', 0),
                    "Easy": total_stats.get('Easy', 0),
                    "Medium": total_stats.get('Medium', 0),
                    "Hard": total_stats.get('Hard', 0)
                }
            },
            "contest_info": {
                "attended": contest.get('attendedContestsCount', 0) if contest else 0,
                "rating": contest.get('rating', 0) if contest else 0,
                "global_ranking": contest.get('globalRanking', 0) if contest else 0,
                "top_percentage": contest.get('topPercentage', 0) if contest else 0
            },
            "badges": [{"name": badge['name'], "icon": badge.get('icon')} for badge in user.get('badges', [])],
            "recent_submissions": submissions[:10]  # Last 10 submissions
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
        leetcode_username = None
        for line in lines:
            if 'leetcode' in line.lower():
                leetcode_username = line.split(':', 1)[1].strip()
                break
    
    if leetcode_username:
        print(f"Processing LeetCode profile: {leetcode_username}")
        
        profile_data = extract_leetcode_profile(leetcode_username)
        
        # Save to JSON file
        with open('leetcode_data.json', 'w') as f:
            json.dump(profile_data, f, indent=2)
        print("✓ LeetCode data saved to leetcode_data.json")
    else:
        print("LeetCode username not found in .env file")
