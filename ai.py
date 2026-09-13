import os
import json
from google import genai
from google.genai import types

def analyze_with_gemini(user_profile: dict, opportunities: list) -> dict:
    """
    Sends the normalized opportunities and user profile to Gemini.
    Forces Gemini to return a structured JSON response.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in environment variables.")

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are CareerAI, an AI career advisor focused on opportunities available to students and professionals in Pakistan.

    Analyze the user's profile and the real-world opportunities provided below.

    User Profile:
    {json.dumps(user_profile, indent=2)}

    Opportunities:
    {json.dumps(opportunities, indent=2)}

    Your tasks:
    1. Rank the most relevant opportunities based on the user's skills, education, and experience.
    2. Explain why each opportunity matches the user's profile.
    3. Identify missing skills (Skill Gaps).
    4. Recommend useful courses from the list or general advice based on skill gaps.
    5. Prioritize realistic opportunities for the user's education and experience.
    6. Prefer opportunities relevant to Pakistan or remote work.
    7. NEVER invent jobs, companies, URLs, deadlines, or requirements. Only use information present in the supplied data.
    8. Output ONLY valid JSON, with no markdown code blocks formatting (no ```json).

    Return exactly this JSON structure:
    {{
      "top_matches": [
        {{
          "title": "...",
          "company": "...",
          "type": "Internship|Job|Course",
          "match_score": 0,
          "why_match": "...",
          "skill_gap": ["..."],
          "url": "..."
        }}
      ],
      "skill_gaps": ["...", "..."],
      "recommended_courses": [
         {{ "title": "...", "provider": "...", "why": "...", "url": "..." }}
      ],
      "career_advice": "...",
      "career_readiness_score": 0
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        )
        
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
            
        analysis_data = json.loads(result_text)
        return analysis_data
        
    except Exception as e:
        print(f"Gemini AI Error: {e}")
        return {
            "top_matches": [],
            "skill_gaps": [],
            "recommended_courses": [],
            "career_advice": "Failed to analyze results with AI. Please check API keys or try again.",
            "career_readiness_score": 0
        }