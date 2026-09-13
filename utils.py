import re

def clean_text(text: str) -> str:
    """Removes excessive whitespace and standardizes text."""
    if not text:
        return "Not specified"
    return re.sub(r'\s+', ' ', str(text)).strip()

def calculate_match_score(user_skills: list, opp_description: str, opp_skills_text: str = "") -> int:
    """
    Calculates a basic relevance score based on skill overlap.
    Returns a percentage (0-100).
    """
    if not user_skills:
        return 0
        
    text_to_search = f"{opp_description} {opp_skills_text}".lower()
    matched_skills = 0
    
    for skill in user_skills:
        if skill.lower() in text_to_search:
            matched_skills += 1
            
    score = int((matched_skills / len(user_skills)) * 100)
    return score

def deduplicate_results(results: list) -> list:
    """Deduplicates opportunities based on normalized title and company/provider."""
    seen = set()
    unique_results = []
    
    for res in results:
        title = str(res.get("title", "")).lower().strip()
        company = str(res.get("company", res.get("provider", ""))).lower().strip()
        
        # Create a unique key for deduplication
        key = f"{title}|{company}"
        
        if key not in seen and title:
            seen.add(key)
            unique_results.append(res)
            
    return unique_results