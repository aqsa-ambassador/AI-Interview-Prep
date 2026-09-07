import streamlit as st
from groq import Groq
import google.generativeai as genai
import json

st.set_page_config(
    page_title="AI Interview Prep Generator",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Interview Prep Generator")
st.write(
    "Enter a job role and generate 10 technical and HR interview "
    "questions with ideal sample answers."
)
st.divider()

groq_key = st.secrets.get("GROQ_API_KEY", "")
google_key = st.secrets.get("GOOGLE_API_KEY", "")

job_title = st.text_input(
    "Job Title",
    placeholder="e.g. Data Analyst, Python Developer"
)

def clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "")
    return json.loads(text.strip())

def generate_with_groq(job_title):
    client = Groq(api_key=groq_key)

    prompt = f"""
You are an expert job interview coach.

Create an interview preparation guide for:
Job Role: {job_title}

Generate exactly 10 questions:
- Approximately 6 technical questions
- Approximately 4 HR/behavioral questions
- Questions must be specific to the job role
- Every question must have an ideal sample answer
- Answers should be professional, practical, concise, and useful
- Return ONLY valid JSON.

Use exactly this structure:
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "Question",
      "answer": "Ideal sample answer"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert interview preparation assistant."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return clean_json(response.choices[0].message.content)

def generate_with_google(job_title):
    genai.configure(api_key=google_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are an expert job interview coach.

Create an interview preparation guide for:
Job Role: {job_title}

Generate exactly 10 questions:
- Approximately 6 technical questions
- Approximately 4 HR/behavioral questions
- Questions must be specific to the job role
- Every question must have an ideal sample answer
- Answers should be professional, practical, concise, and useful
- Return ONLY valid JSON.

Use exactly this structure:
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "Question",
      "answer": "Ideal sample answer"
    }}
  ]
}}
"""

    response = model.generate_content(prompt)
    return clean_json(response.text)

if st.button("🚀 Generate Interview Questions", use_container_width=True):
    if not job_title.strip():
        st.warning("Please enter a job title.")
    elif not groq_key and not google_key:
        st.error(
            "No API key found. Add GROQ_API_KEY or GOOGLE_API_KEY "
            "in Streamlit Cloud Secrets."
        )
    else:
        with st.spinner("Generating your interview preparation..."):
            try:
                if groq_key:
                    result = generate_with_groq(job_title)
                else:
                    result = generate_with_google(job_title)

                st.session_state["questions"] = result["questions"]

            except Exception as e:
                st.error("Something went wrong while generating questions.")
                st.code(str(e))

if "questions" in st.session_state:
    st.divider()
    st.subheader(f"📚 Interview Preparation: {job_title}")

    for index, item in enumerate(st.session_state["questions"], start=1):
        with st.expander(
            f"{index}. {item.get('question', '')}",
            expanded=False
        ):
            st.markdown(f"**Type:** {item.get('type', 'Interview')}")
            st.markdown("### 💡 Ideal Sample Answer")
            st.write(item.get("answer", ""))

    st.success("Your interview preparation guide is ready!")
