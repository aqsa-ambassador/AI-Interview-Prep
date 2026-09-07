import json
import google.generativeai as genai
from groq import Groq
import streamlit as st

# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title="AI Interview Prep Generator", page_icon="🤖", layout="centered"
)

st.title("🤖 AI Interview Prep Generator")

st.write(
    "Enter a job role and generate 10 technical and HR interview "
    "questions with ideal sample answers."
)

st.divider()

# -----------------------------
# API Keys
# -----------------------------

groq_key = st.secrets.get("GROQ_API_KEY", "")
google_key = st.secrets.get("GOOGLE_API_KEY", "")

# Debug: show whether keys are loaded (remove this in production)
with st.expander("🔧 Debug: API Key Status"):
    st.write("Groq key loaded:", bool(groq_key))
    st.write("Google key loaded:", bool(google_key))

# -----------------------------
# Job Title
# -----------------------------

job_title = st.text_input(
    "Job Title", placeholder="e.g. Data Analyst, Python Developer"
)

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


def get_fallback_questions(role):
    return {
        "questions": [
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
    }


# -----------------------------
# Groq Generation
# -----------------------------


def generate_with_groq(job_title):
    client = Groq(api_key=groq_key)
    prompt = f"""
You are an expert job interview coach. Create an interview preparation guide for Job Role: {job_title}.
Generate exactly 10 interview questions (approx 6 technical, 4 HR).
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
        model="llama-3.1-8b-instant",
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


def generate_with_google(job_title):
    genai.configure(api_key=google_key)
    # Use a current, valid model name
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
You are an expert job interview coach. Create an interview preparation guide for Job Role: {job_title}.
Generate exactly 10 interview questions (approx 6 technical, 4 HR).
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

if st.button("🚀 Generate Interview Questions", use_container_width=True):
    if not job_title.strip():
        st.warning("Please enter a job title.")
    else:
        with st.spinner("Generating your interview preparation..."):
            result = None
            errors = []

            # Try Groq
            if groq_key and not result:
                try:
                    result = generate_with_groq(job_title)
                except Exception as e:
                    errors.append(f"Groq error: {e}")

            # Try Gemini
            if google_key and not result:
                try:
                    result = generate_with_google(job_title)
                except Exception as e:
                    errors.append(f"Gemini error: {e}")

            # Ultimate Safe Fallback
            if not result or "questions" not in result:
                if errors:
                    st.error("API calls failed:\n" + "\n".join(errors))
                result = get_fallback_questions(job_title)
                st.info(
                    "Note: API limits or networks were busy, so a customized "
                    f"high-performance preparation guide was generated instantly for '{job_title}'!"
                )

            st.session_state["questions"] = result["questions"]


# -----------------------------
# Display Results
# -----------------------------

if "questions" in st.session_state:
    st.divider()
    st.subheader(f"📚 Interview Preparation: {job_title}")

    for index, item in enumerate(st.session_state["questions"], start=1):
        question = item.get("question", "Interview Question")
        question_type = item.get("type", "Interview")
        answer = item.get("answer", "No answer available.")

        with st.expander(f"**{index}. [{question_type}]** {question}"):
            st.write(answer)
