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


# -----------------------------
# App Title
# -----------------------------

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
# Groq (Primary)
# -----------------------------


def generate_with_groq(job_title):
  client = Groq(api_key=groq_key)

  prompt = f"""
You are an expert job interview coach.

Create an interview preparation guide for:

Job Role: {job_title}

Generate exactly 10 interview questions.

Requirements:
- Approximately 6 technical questions
- Approximately 4 HR/behavioral questions
- Questions must be specific to the job role
- Every question must have an ideal sample answer
- Answers should be professional, practical, concise, and useful
- Do not include markdown
- Return ONLY valid JSON

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
              "content": "You are an expert interview preparation assistant.",
          },
          {"role": "user", "content": prompt},
      ],
      temperature=0.7,
  )

  return clean_json(response.choices[0].message.content)


# -----------------------------
# Google Gemini (Backup)
# -----------------------------


def generate_with_google(job_title):
  genai.configure(api_key=google_key)
  model = genai.GenerativeModel("gemini-1.5-flash")

  prompt = f"""
You are an expert job interview coach.

Create an interview preparation guide for:

Job Role: {job_title}

Generate exactly 10 interview questions.

Requirements:
- Approximately 6 technical questions
- Approximately 4 HR/behavioral questions
- Questions must be specific to the job role
- Every question must have an ideal sample answer
- Answers should be professional, practical, concise, and useful
- Do not include markdown
- Return ONLY valid JSON

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


# -----------------------------
# Generate Button
# -----------------------------

if st.button("🚀 Generate Interview Questions", use_container_width=True):
  if not job_title.strip():
    st.warning("Please enter a job title.")

  elif not groq_key and not google_key:
    st.error(
        "No API key found. Please add GROQ_API_KEY or GOOGLE_API_KEY in"
        " Streamlit Cloud Secrets."
    )

  else:
    with st.spinner("Generating your interview preparation..."):
      result = None

      # Try Groq first (Primary to avoid Gemini quota issues)
      if groq_key:
        try:
          result = generate_with_groq(job_title)
        except Exception as e:
          st.info("Groq encountered an issue. Trying Gemini backup...")

      # Fallback to Gemini if Groq failed
      if not result and google_key:
        try:
          result = generate_with_google(job_title)
        except Exception as e:
          st.error(f"Gemini error: {str(e)}")

      if result and "questions" in result:
        st.session_state["questions"] = result["questions"]
      else:
        st.error(
            "Could not generate questions. Please check your API keys or limits."
        )


# -----------------------------
# Display Results
# -----------------------------

if "questions" in st.session_state:
  st.divider()

  st.subheader(f"📚 Interview Preparation: {job_title}")

  for index, item in enumerate(st.session_state["questions"], start=1):
    question = item.get("question", "Interview Question")
    question_type = item.get("type", "Interview")
    answer = item.get("answer", "No answer generated.")

    with st.expander(f"{index}. {question}", expanded=False):
      st.markdown(f"**Type:** {question_type}")
      st.markdown("### 💡 Ideal Sample Answer")
      st.write(answer)

  st.success("Your interview preparation guide is ready! 🎉")
