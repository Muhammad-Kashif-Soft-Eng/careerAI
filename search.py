import os
import requests
from utils import deduplicate_results, calculate_match_score, clean_text

def generate_queries(profile: dict) -> list:
    """Dynamically generates a lean set of search queries based on the user's profile."""
    field = profile.get("field", "Software")
    location = profile.get("location", "Pakistan")
    skills = " ".join(profile.get("skills", [])[:2])
    
    if location.lower() == "any":
        location = "Pakistan OR Remote"

    # Reduced from 6 queries to 3 queries to prevent SerpAPI timeouts on free tier
    queries = [
        f"{field} internship {location} {skills}",
        f"junior {field} jobs {location} {skills}",
        f"{skills} training course Pakistan"
    ]
    
    return queries

def search_web(query: str) -> list:
    """Executes a web search. Uses SerpAPI Google Search REST API."""
    api_key = os.environ.get("SEARCH_API_KEY")
    if not api_key:
        print("Warning: SEARCH_API_KEY missing. Returning empty results.")
        return []

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 5, 
        "gl": "pk", 
    }
    
    try:
        # Added a larger 45-second read timeout for slower connections
        response = requests.get("https://serpapi.com/search", params=params, timeout=(10, 45))
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        for item in data.get("organic_results", []):
            results.append({
                "title": clean_text(item.get("title")),
                "company": clean_text(item.get("source")),
                "type": "Course" if "course" in query.lower() or "training" in query.lower() else "Job/Internship",
                "location": "Pakistan / Online",
                "description": clean_text(item.get("snippet")),
                "url": item.get("link", "#"),
                "source": "Web Search"
            })
            
        return results
    except Exception as e:
        print(f"Search API error for query '{query}': {e}")
        return []

def collect_opportunities(profile: dict) -> list:
    """Main pipeline to generate queries, fetch, clean, and filter results."""
    queries = generate_queries(profile)
    all_results = []
    
    for q in queries:
        all_results.extend(search_web(q))
        
    unique_results = deduplicate_results(all_results)
    
    user_skills = profile.get("skills", [])
    for res in unique_results:
        res["basic_score"] = calculate_match_score(user_skills, res["description"], res["title"])
        
        text = f"{res['title']} {res['description']}".lower()
        if "intern" in text:
            res["type"] = "Internship"
        elif "course" in text or "certification" in text or "training" in text:
            res["type"] = "Course"
        else:
            res["type"] = "Job"

    unique_results.sort(key=lambda x: x["basic_score"], reverse=True)
    return unique_results[:15]