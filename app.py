import streamlit as st
import os
from dotenv import load_dotenv
from search import collect_opportunities
from ai import analyze_with_gemini

# Load environment variables
load_dotenv()

# Configure Page
st.set_page_config(
    page_title="CareerAI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Customizations ---
st.markdown("""
    <style>
    .match-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .dark .match-card {
        background-color: #1e1e1e;
        border-color: #333;
    }
    .tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 15px;
        background-color: #e3f2fd;
        color: #1976d2;
        font-size: 0.85em;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🎯 CareerAI")
st.markdown("""
**AI-powered career opportunities for Pakistan**  
Find internships, jobs, and courses matched to your skills and education.
""")
st.divider()

# --- User Profile Form ---
st.subheader("YOUR PROFILE")

col1, col2 = st.columns(2)

with col1:
    education = st.selectbox("Education Level", [
        "Matric", "Intermediate", "Diploma", "Bachelor's", "Master's", "MPhil", "PhD", "Other"
    ])
    degree = st.selectbox("Degree / Program", [
        "Computer Science", "Software Engineering", "Information Technology", 
        "Artificial Intelligence", "Data Science", "Cyber Security", 
        "Electrical Engineering", "Business", "Accounting & Finance", "Marketing", "Other"
    ])
    field = st.selectbox("Preferred Career Field", [
        "Software Development", "Web Development", "Mobile Development", 
        "AI / Machine Learning", "Data Science", "Cyber Security", 
        "Cloud / DevOps", "UI/UX", "Business", "Marketing", "Finance", "Engineering", "Other"
    ])

with col2:
    experience = st.selectbox("Experience Level", [
        "Student", "Fresh Graduate", "Beginner", "0–1 years", "1–3 years", "3+ years"
    ])
    location = st.selectbox("Preferred Location", [
        "Pakistan", "Islamabad", "Rawalpindi", "Lahore", "Karachi", 
        "Peshawar", "Multan", "Faisalabad", "Remote", "Any"
    ])
    skills = st.multiselect("Skills (Select all that apply)", [
        "Python", "JavaScript", "React", "Node.js", "Java", "C++", "SQL",
        "Machine Learning", "Data Analysis", "UI/UX", "HTML", "CSS", 
        "Tailwind", "MongoDB", "AWS", "Git", "Docker", "FastAPI", "PostgreSQL"
    ])

# --- Main Action ---
st.divider()

if st.button("🔎 Find Opportunities", type="primary", use_container_width=True):
    if not skills:
        st.warning("Please select at least one skill so we can find relevant matches.")
        st.stop()
        
    if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("SEARCH_API_KEY"):
        st.error("API Keys missing! Please configure GEMINI_API_KEY and SEARCH_API_KEY in your .env file.")
        st.stop()
        
    profile = {
        "education": education,
        "degree": degree,
        "field": field,
        "experience": experience,
        "location": location,
        "skills": skills
    }
    
    with st.status("Analyzing your profile...", expanded=True) as status:
        st.write("🔎 Generating career searches...")
        
        st.write("🌐 Searching real-world opportunities (this may take a moment)...")
        raw_opportunities = collect_opportunities(profile)
        
        if not raw_opportunities:
            status.update(label="Search Failed", state="error", expanded=False)
            st.error("We couldn't retrieve live opportunities right now. Please try again later.")
            st.stop()
            
        st.write(f"✅ {len(raw_opportunities)} relevant opportunities discovered and cleaned.")
        
        st.write("🤖 CareerAI is analyzing your results...")
        ai_analysis = analyze_with_gemini(profile, raw_opportunities)
        
        status.update(label="Analysis Complete!", state="complete", expanded=False)
        
    # Store results in session state so they survive re-renders
    st.session_state["results"] = ai_analysis

# --- Display Results ---
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    
    st.divider()
    st.subheader("RESULTS")
    
    tab_internships, tab_jobs, tab_courses, tab_insights = st.tabs([
        "Internships", "Jobs", "Courses", "🤖 AI Insights"
    ])
    
    # Helper to render cards
    def render_match_card(match):
        gap_str = ", ".join(match.get("skill_gap", [])) if match.get("skill_gap") else "None detected"
        url = match.get("url", "#")
        
        st.markdown(f"""
        <div class="match-card">
            <h4 style="margin-top:0;">{match.get('title', 'Position')}</h4>
            <p style="color: gray; margin-bottom: 5px;"><strong>{match.get('company', 'Unknown')}</strong></p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 1.2em; font-weight: bold; color: #4CAF50;">Match: {match.get('match_score', 0)}%</span>
            </div>
            <p><strong>Why it matches:</strong> {match.get('why_match', '')}</p>
            <p><strong>Skill Gap:</strong> <span style="color: #d32f2f;">{gap_str}</span></p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("View Opportunity", url=url)
        st.write("") # Spacer
        
    with tab_internships:
        internships = [m for m in results.get("top_matches", []) if m.get("type", "").lower() == "internship"]
        if internships:
            for i in internships:
                render_match_card(i)
        else:
            st.info("No strong internship matches found based on your profile.")

    with tab_jobs:
        jobs = [m for m in results.get("top_matches", []) if m.get("type", "").lower() == "job"]
        if jobs:
            for j in jobs:
                render_match_card(j)
        else:
            st.info("No strong job matches found. Try adding more skills or broadening your location.")
            
    with tab_courses:
        courses = [m for m in results.get("top_matches", []) if m.get("type", "").lower() == "course"]
        # Append AI recommended courses
        ai_courses = results.get("recommended_courses", [])
        
        if courses or ai_courses:
            for c in courses:
                render_match_card(c)
            
            if ai_courses:
                st.markdown("### 📚 Recommended by CareerAI")
                for ac in ai_courses:
                    with st.expander(f"{ac.get('title')} - {ac.get('provider')}"):
                        st.write(f"**Why:** {ac.get('why')}")
                        st.link_button("Go to Course", url=ac.get('url', '#'))
        else:
            st.info("No specific courses found. Check AI Insights for skill gaps.")

    with tab_insights:
        st.markdown("### 🤖 CareerAI Insights")
        
        col_score, col_text = st.columns([1, 3])
        with col_score:
            st.metric("Career Readiness", f"{results.get('career_readiness_score', 0)}%")
            st.progress(results.get('career_readiness_score', 0) / 100)
            
        with col_text:
            st.markdown(f"**Analysis:** {results.get('career_advice', 'Keep building your skills!')}")
            
            st.markdown("#### Top Skill Gaps")
            gaps = results.get("skill_gaps", [])
            if gaps:
                for gap in gaps:
                    st.markdown(f"- 🔴 {gap}")
            else:
                st.success("You are well aligned with current opportunities!")