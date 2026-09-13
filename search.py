import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils import deduplicate_results, calculate_match_score, clean_text

def get_robust_session():
    """Creates a network session that automatically retries failed requests."""
    session = requests.Session()
    # Retry up to 3 times if the network drops or times out
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def generate_queries(profile: dict) -> list:
    field = profile.get("field", "Software")
    location = profile.get("location", "Pakistan")
    skills = " ".join(profile.get("skills", [])[:2])
    
    if location.lower() == "any":
        location = "Pakistan OR Remote"

    queries = [
        f"{field} internship {location} {skills}",
        f"junior {field} jobs {location} {skills}",
        f"{skills} training course Pakistan"
    ]
    return queries

def search_web(query: str) -> list:
    api_key = os.environ.get("SEARCH_API_KEY")
    if not api_key:
        print("Warning: SEARCH_API_KEY missing.")
        return []

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 5, 
        "gl": "pk", 
    }
    
    session = get_robust_session()
    
    try:
        # Using a generous 45-second timeout for unstable connections
        response = session.get("https://serpapi.com/search", params=params, timeout=(15, 45))
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