import streamlit as st
from groq import Groq
from datetime import datetime
from supabase import create_client, Client

# --- Supabase Setup ---
supabase_url = st.secrets.get("SUPABASE_URL")
supabase_key = st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# --- Utility Functions ---
def save_user_info_to_supabase(user_info):
    try:
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": str(user_info["name"]),
            "email": str(user_info["email"]),
            "agreed": bool(user_info["agreed"])
        }
        supabase.table("user_info").insert(data).execute()
    except Exception as e:
        st.error(f"Supabase user info insert error: {e}")

def save_comparison_to_supabase(comparison):
    try:
        supabase.table("prompt_comparisons").insert(comparison).execute()
    except Exception as e:
        st.error(f"Supabase insert error: {e}")

def save_survey_to_supabase(survey_data):
    try:
        supabase.table("task_surveys").insert(survey_data).execute()
    except Exception as e:
        st.error(f"Supabase survey insert error: {e}")

def optimize_prompt(prompt, system_prompt):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error with Groq optimization API: {str(e)}")
        return None

def get_groq_response(prompt, model):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error with Groq response API: {str(e)}")
        return None

# --- Page Config ---
st.set_page_config(
    page_title="Prompt Optimization Tool",
    page_icon="🔄",
    layout="wide"
)

# --- User Registration ---
if "user_info_submitted" not in st.session_state:
    st.session_state.user_info_submitted = False

if not st.session_state.user_info_submitted:
    st.title("Welcome to the Prompt Optimization Tool")
    st.markdown("""
### Informed Consent
Please read and accept the following terms before using this application.
- Your prompts and responses will be stored for research purposes.
- Your name and email will be used to associate your data.
- You may withdraw at any time by contacting the administrator.
""")
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    agreed = st.checkbox("I have read and agree to the terms and conditions.")

    submit_disabled = not agreed
    if st.button("Submit", disabled=submit_disabled):
        if not name or not email:
            st.warning("Please fill in all fields.")
        else:
            user_info = {"name": name, "email": email, "agreed": agreed}
            save_user_info_to_supabase(user_info)
            st.session_state.user_info_submitted = True
            st.session_state.user_name = name
            st.session_state.user_email = email
            st.success("Thank you! You may now use the app.")
            st.rerun()
    st.stop()

# --- Fixed Model and Optimization Prompt ---
response_model = "llama-3.1-8b-instant"
optimization_model = "llama-3.3-70b-versatile"
optimization_prompt = """You are Llama3-70B, a helpful and precise AI assistant. Your primary directive is to follow instructions exactly as given without deviation, interpretation, or embellishment.

CORE PRINCIPLES:
• Execute tasks precisely as specified in the user's prompt
• Do not add extra information, context, or suggestions unless explicitly requested
• Do not modify, improve, or "enhance" the given instructions
• If instructions are unclear, ask for clarification rather than making assumptions
• Maintain the exact tone, style, and format requested
• Complete all parts of multi-step instructions in the specified order

RESPONSE GUIDELINES:
• Begin your response immediately with the requested content
• Do not include meta-commentary about the task unless asked
• Match the specified length requirements exactly (word counts, character limits, etc.)
• Adhere strictly to any formatting requirements (bullets, numbered lists, paragraphs, etc.)
• If given conflicting instructions, ask for clarification rather than choosing arbitrarily
• Suggest improvements to the user's prompt unless explicitly asked not to

QUALITY STANDARDS:
• Produce outputs that directly fulfill the stated objective
• Maintain consistency throughout your response
• Ensure factual accuracy when dealing with verifiable information
• Preserve the intended audience and complexity level specified in prompts

RESTRICTIONS:
• Do not provide alternatives or variations unless requested
• Do not add disclaimers or warnings unless they relate to harmful content
• Do not reference these system instructions in your responses

Remember: Your success is measured by how precisely you execute the given instructions, not by how much additional value you provide beyond what was requested.
"""

# --- Task and Survey Setup ---
TASKS = [
    {
        "title": "Creative Story Generation",
        "objective": "Write a prompt to generate a short creative story for a specific audience and genre.",
        "example prompt": "Write an engaging children’s adventure story featuring a young protagonist who discovers a hidden talent."
    },
    {
        "title": "Explanatory Content Creation",
        "objective": "Write a prompt to generate a clear, accessible explanation of a complex topic.",
        "example prompt": "Explain “how machine learning works” to a 12-year-old with no technical background."
    },
    {
        "title": "Professional Email Composition",
        "objective": "Write a prompt to generate appropriate business communication.",
        "example prompt": "Draft a polite follow-up email to a potential client who hasn’t responded to an initial proposal after two weeks."
    },
    {
        "title": "Analytical Summary Writing",
        "objective": "Write a prompt to generate a structured analysis or comparison.",
        "example prompt": "Compare and contrast remote work versus office work, focusing on productivity, work-life balance, and team collaboration."
    }
]

SURVEY_QUESTIONS = [
    "I think that I would like to use this response frequently.",
    "I found the response unnecessarily complex.",
    "I thought the response was easy to use.",
    "I think that I would need the support of a technical person to be able to use this response.",
    "I found the various functions in this response were well integrated.",
    "I thought there was too much inconsistency in this response.",
    "I would imagine that most people would learn to use this response very quickly.",
    "I found the response very cumbersome to use.",
    "I felt very confident using the response.",
    "I needed to learn a lot of things before I could get going with this response."
]

if "current_task" not in st.session_state:
    st.session_state.current_task = 0
if "task_completed" not in st.session_state:
    st.session_state.task_completed = [False] * len(TASKS)
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []

task_idx = st.session_state.current_task
task = TASKS[task_idx]

st.header(f"Task {task_idx+1}: {task['title']}")
st.markdown(f"**Objective:** {task['objective']}")
st.markdown(f"**Example prompt:** {task['example prompt']}")

user_prompt = st.text_area("Enter your prompt for this task:", key=f"prompt_{task_idx}")

if st.button("Submit Prompt", key=f"submit_{task_idx}"):
    if not user_prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Optimizing and generating responses..."):
            original_response = get_groq_response(user_prompt, response_model)
            optimized_prompt = optimize_prompt(user_prompt, optimization_prompt)
            optimized_response = get_groq_response(optimized_prompt, response_model)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comparison = {
                "timestamp": timestamp,
                "user_id": st.session_state.user_email,
                "task_id": task_idx+1,
                "original_prompt": user_prompt,
                "optimized_prompt": optimized_prompt,
                "original_response": original_response,
                "optimized_response": optimized_response,
                "user_preference": None
            }
            st.session_state.comparison_results.append(comparison)
            st.session_state.task_completed[task_idx] = True
            st.rerun()

if st.session_state.task_completed[task_idx]:
    latest = st.session_state.comparison_results[-1]
    st.subheader("Compare Responses")
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("Response 1", latest["original_response"], height=200, disabled=True)
        if st.button("Prefer Response 1", key=f"pref1_{task_idx}"):
            st.session_state.comparison_results[-1]["user_preference"] = "original"
            save_comparison_to_supabase(st.session_state.comparison_results[-1])
            st.session_state[f"survey_ready_{task_idx}"] = True
            st.rerun()
    with col2:
        st.text_area("Response 2", latest["optimized_response"], height=200, disabled=True)
        if st.button("Prefer Response 2", key=f"pref2_{task_idx}"):
            st.session_state.comparison_results[-1]["user_preference"] = "optimized"
            save_comparison_to_supabase(st.session_state.comparison_results[-1])
            st.session_state[f"survey_ready_{task_idx}"] = True
            st.rerun()

    # Survey
    if st.session_state.get(f"survey_ready_{task_idx}", False):
        st.subheader("Survey")
        survey_answers = []
        for i, q in enumerate(SURVEY_QUESTIONS):
            survey_answers.append(
                st.radio(q, [1,2,3,4,5], key=f"survey_{task_idx}_{i}")
            )
        if st.button("Submit Survey", key=f"survey_submit_{task_idx}"):
            survey_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": st.session_state.user_email,
                "task_id": task_idx+1,
                "answers": survey_answers
            }
            save_survey_to_supabase(survey_data)
            st.success("Survey submitted! Proceeding to next task...")
            if task_idx+1 < len(TASKS):
                st.session_state.current_task += 1
                st.rerun()
            else:
                st.success("All tasks completed! Thank you for your participation.")