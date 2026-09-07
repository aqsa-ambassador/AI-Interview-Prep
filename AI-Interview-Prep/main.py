import json
import google.generativeai as genai
from groq import Groq
import streamlit as st

# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title="AI Interview Prep Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Custom Styling
# -----------------------------

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 2rem; max-width: 1000px; }
    .app-header {
        text-align: center;
        padding: 1.2rem 0 0.4rem 0;
    }
    .app-header h1 { margin-bottom: 0.2rem; }
    .app-subtitle { color: #9aa0a6; font-size: 1.05rem; }
    .qa-card {
        border: 1px solid rgba(150,150,150,0.25);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    .badge-technical {
        background: #1f6feb22; color: #58a6ff;
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600; border: 1px solid #1f6feb55;
    }
    .badge-hr {
        background: #ff8c0022; color: #ffa657;
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600; border: 1px solid #ff8c0055;
    }
    .q-index { color: #888; font-size: 0.8rem; margin-right: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header
# -----------------------------

st.markdown(
    """
    <div class="app-header">
        <h1>🤖 AI Interview Prep Generator</h1>
        <div class="app-subtitle">Generate tailored technical & HR interview questions with ideal sample answers.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# -----------------------------
# API Keys
# -----------------------------

groq_key = st.secrets.get("GROQ_API_KEY", "")
google_key = st.secrets.get("GOOGLE_API_KEY", "")

# -----------------------------
# Sidebar: Settings & Status
# -----------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    num_questions = st.slider("Number of questions", min_value=4, max_value=15, value=10)
    tech_ratio = st.slider("Technical questions (%)", min_value=20, max_value=90, value=60, step=10)
    difficulty = st.selectbox("Difficulty level", ["Beginner", "Intermediate", "Advanced"], index=1)

    st.divider()
    st.subheader("🔌 Connection Status")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Groq", "✅ Ready" if groq_key else "❌ Missing")
    with col_b:
        st.metric("Gemini", "✅ Ready" if google_key else "❌ Missing")

    with st.expander("Debug details"):
        st.write("Groq key loaded:", bool(groq_key))
        st.write("Google key loaded:", bool(google_key))

    st.divider()
    st.caption("Add your API keys in `.streamlit/secrets.toml` as `GROQ_API_KEY` and `GOOGLE_API_KEY`.")

# -----------------------------
# Main Input Area
# -----------------------------

col1, col2 = st.columns([4, 1])
with col1:
    job_title = st.text_input(
        "Job Title", placeholder="e.g. Data Analyst, Python Developer", label_visibility="visible"
    )
with col2:
    st.write("")
    st.write("")
    generate_clicked = st.button("🚀 Generate", use_container_width=True, type="primary")

st.divider()

# -----------------------------
# Clean JSON Response
# -----------------------------


def clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "")
    return json.loads(text.strip())


# -----------------------------
# Fallback Smart Generator (Never Fails)
# -----------------------------


def get_fallback_questions(role, n_questions=10, tech_pct=60):
    n_tech = max(1, round(n_questions * tech_pct / 100))
    n_hr = max(1, n_questions - n_tech)

    technical_pool = [
        {
            "type": "Technical",
            "question": f"Can you explain the core responsibilities and daily workflows of a {role}?",
            "answer": f"As a {role}, core responsibilities include designing, developing, and optimizing solutions while collaborating with cross-functional teams to meet project goals.",
        },
        {
            "type": "Technical",
            "question": "What tools, programming languages, or frameworks do you consider essential for this role?",
            "answer": "Essential tools depend on the stack, but typically include industry-standard programming languages, version control systems, and analytical frameworks tailored to efficient problem-solving.",
        },
        {
            "type": "Technical",
            "question": "How do you handle debugging or performance optimization in complex projects?",
            "answer": "I isolate the bottleneck using profiling tools or logs, write targeted unit tests, and refactor the code logically to improve execution speed and maintainability.",
        },
        {
            "type": "Technical",
            "question": "Describe a challenging technical problem you solved recently.",
            "answer": "I analyzed the root cause, broke down the problem into manageable components, implemented a scalable fix, and documented the process to prevent future occurrences.",
        },
        {
            "type": "Technical",
            "question": "How do you ensure code quality and maintainability in your work?",
            "answer": "By following clean coding standards, writing comprehensive documentation, conducting peer code reviews, and utilizing automated testing.",
        },
        {
            "type": "Technical",
            "question": "How do you stay updated with new trends and advancements related to this field?",
            "answer": "I regularly read documentation, follow industry blogs, take specialized online courses, and experiment with new technologies in personal projects.",
        },
    ]

    hr_pool = [
        {
            "type": "HR",
            "question": "Tell me about yourself and your professional background.",
            "answer": f"I am a passionate professional specializing in {role}, with a strong foundation in problem-solving, continuous learning, and delivering impactful results.",
        },
        {
            "type": "HR",
            "question": "Why do you want to work with us in this specific role?",
            "answer": "Your company's innovative culture and dedication to quality align perfectly with my career goals and values.",
        },
        {
            "type": "HR",
            "question": "How do you handle tight deadlines and high-pressure situations?",
            "answer": "I prioritize tasks using structured frameworks, maintain clear communication with stakeholders, and focus on delivering high-impact deliverables efficiently.",
        },
        {
            "type": "HR",
            "question": "Where do you see your professional career in the next five years?",
            "answer": "I aim to grow into a senior leadership or architectural role where I can lead high-performing teams and drive strategic technical initiatives.",
        },
    ]

    questions = (technical_pool * 3)[:n_tech] + (hr_pool * 3)[:n_hr]
    return {"questions": questions}


# -----------------------------
# Groq Generation
# -----------------------------


def generate_with_groq(job_title, n_questions, tech_pct, difficulty):
    client = Groq(api_key=groq_key)
    n_tech = max(1, round(n_questions * tech_pct / 100))
    n_hr = max(1, n_questions - n_tech)
    prompt = f"""
You are an expert job interview coach. Create an interview preparation guide for Job Role: {job_title}.
Difficulty level: {difficulty}.
Generate exactly {n_questions} interview questions ({n_tech} technical, {n_hr} HR).
Return ONLY valid JSON with this exact structure, no extra text:
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "Question text",
      "answer": "Ideal sample answer"
    }}
  ]
}}
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are an expert interview assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return clean_json(response.choices[0].message.content)


# -----------------------------
# Google Gemini Generation
# -----------------------------


def generate_with_google(job_title, n_questions, tech_pct, difficulty):
    genai.configure(api_key=google_key)
    model = genai.GenerativeModel("gemini-3.6-flash")
    n_tech = max(1, round(n_questions * tech_pct / 100))
    n_hr = max(1, n_questions - n_tech)
    prompt = f"""
You are an expert job interview coach. Create an interview preparation guide for Job Role: {job_title}.
Difficulty level: {difficulty}.
Generate exactly {n_questions} interview questions ({n_tech} technical, {n_hr} HR).
Return ONLY valid JSON with this exact structure, no extra text:
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "Question text",
      "answer": "Ideal sample answer"
    }}
  ]
}}
"""
    response = model.generate_content(prompt)
    return clean_json(response.text)


# -----------------------------
# Generate Button & Logic
# -----------------------------

if generate_clicked:
    if not job_title.strip():
        st.warning("Please enter a job title.")
    else:
        progress = st.progress(0, text="Starting generation...")
        result = None
        errors = []
        source_used = "Fallback"

        if groq_key and not result:
            progress.progress(30, text="Trying Groq...")
            try:
                result = generate_with_groq(job_title, num_questions, tech_ratio, difficulty)
                source_used = "Groq"
            except Exception as e:
                errors.append(f"Groq error: {e}")

        if google_key and not result:
            progress.progress(65, text="Trying Gemini...")
            try:
                result = generate_with_google(job_title, num_questions, tech_ratio, difficulty)
                source_used = "Gemini"
            except Exception as e:
                errors.append(f"Gemini error: {e}")

        progress.progress(90, text="Finalizing...")

        if not result or "questions" not in result:
            if errors:
                with st.expander("⚠️ API errors (click to view)"):
                    for err in errors:
                        st.error(err)
            result = get_fallback_questions(job_title, num_questions, tech_ratio)
            st.info(
                f"Note: API limits or networks were busy, so a customized "
                f"preparation guide was generated instantly for '{job_title}'!"
            )

        progress.progress(100, text="Done!")
        progress.empty()

        st.session_state["questions"] = result["questions"]
        st.session_state["job_title_used"] = job_title
        st.session_state["source_used"] = source_used


# -----------------------------
# Display Results
# -----------------------------

if "questions" in st.session_state:
    questions = st.session_state["questions"]
    job_title_used = st.session_state.get("job_title_used", job_title)
    source_used = st.session_state.get("source_used", "Fallback")

    tech_count = sum(1 for q in questions if q.get("type", "").lower() == "technical")
    hr_count = len(questions) - tech_count

    st.subheader(f"📚 Interview Preparation: {job_title_used}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Questions", len(questions))
    m2.metric("Technical", tech_count)
    m3.metric("HR", hr_count)

    st.caption(f"Generated via: **{source_used}**")

    tab_all, tab_tech, tab_hr = st.tabs(["📋 All", "🛠️ Technical", "🧑‍💼 HR"])

    def render_questions(items, offset=1):
        for index, item in enumerate(items, start=offset):
            question = item.get("question", "Interview Question")
            question_type = item.get("type", "Interview")
            answer = item.get("answer", "No answer available.")
            badge_class = "badge-technical" if question_type.lower() == "technical" else "badge-hr"

            st.markdown(
                f"""
                <div class="qa-card">
                    <span class="q-index">Q{index}</span>
                    <span class="{badge_class}">{question_type}</span>
                    <p style="margin: 0.5rem 0 0.3rem 0; font-weight: 600;">{question}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("💡 Show sample answer"):
                st.write(answer)

    with tab_all:
        render_questions(questions)

    with tab_tech:
        render_questions([q for q in questions if q.get("type", "").lower() == "technical"])

    with tab_hr:
        render_questions([q for q in questions if q.get("type", "").lower() == "hr"])

    st.divider()

    # Download as text
    lines = [f"Interview Preparation: {job_title_used}\n"]
    for i, q in enumerate(questions, start=1):
        lines.append(f"{i}. [{q.get('type', 'Interview')}] {q.get('question', '')}")
        lines.append(f"   Answer: {q.get('answer', '')}\n")
    download_text = "\n".join(lines)

    st.download_button(
        "⬇️ Download as Text",
        data=download_text,
        file_name=f"interview_prep_{job_title_used.replace(' ', '_').lower()}.txt",
        mime="text/plain",
        use_container_width=True,
    )
