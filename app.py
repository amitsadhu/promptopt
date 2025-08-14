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
### Informed Consent of Participation
You are invited to participate in the online study "Prompt, Revise, Repeat". The study is conducted by Amit Ephraim Sadhu, Joseph Anthony, and Ramya Sai Murali and supervised by Prof. Dr. Valentin Schwind from the Frankfurt University of Applied Sciences. The study with estimated 24 participants takes place in the period from 2025-08-15 to 2025-08-29.

**Please note:**
- Your participation is entirely voluntary and can be discontinued or withdrawn at any time.
- For the evaluation, we collect some personal information (e.g., age, gender, etc.), whereas contact data (e.g. e-mails) will only be used for feedback or further information about the study and not be passed on to any third parties.
- One session of the online study will last ca. 30 minutes.
- As compensation for your participation, you will receive one credit point for the lecture.
- During the session, we will log your input and manually record notes.
- Recordings and personal data are subject to the guidelines of the General Data Protection Regulation (GDPR) and will be pseudoanonymized (with a coded number) stored, evaluated, and potentially published so that without information from the researchers no conclusions can be drawn about individual persons.
- The alternative to participation in this study is to choose not to participate. If you have any questions, concerns, or complaints about the informed consent process of this research study or your rights as a human research subject, please contact Prof. Dr. Valentin Schwind. Please read the following information carefully and take the time you need.

#### 1. Purpose and Goal of this Research
We aim to understand if an automated prompt optimization system helps novice users. The goal of our study is to improve the user experience of novice LLM users. Your participation will help us achieve this research goal. The results of this research may be presented at scientific or professional meetings or published in scientific proceedings and journals.

#### 2. Study Participation
Your participation in this online study is entirely voluntary and can be discontinued or withdrawn at any time. You can refuse to answer any questions or continue with the study at any time if you feel uncomfortable in any way. You can discontinue or withdraw your participation at any time without giving a reason. However, we reserve the right to exclude you from the study (e.g., with invalid trials or if continuing the study could have a negative impact on your well-being or the equipment). You will also receive the compensation offered if you discontinue study participation. Repeated participation in the study is not permitted.

#### 3. Study Procedure
After confirming this informed consent the procedure is as follows:
- Complete the task assigned
- Complete the survey associated with the task
- Repeat step 2 & 3 for the remaining tasks
- Complete the final survey

The confirmation of participation in this study can be obtained directly from the researchers.

#### 4. Risks and Benefits
In the online study you will not be exposed to any immediate risk or danger. As with all computer systems on which data is processed, despite security measures, there is a small risk of data leakage and the loss of confidential or personal information. As compensation for your participation, you will receive one credit point for the lecture. With your participation you support our research work and contribute to a better understanding of human-computer interaction.

#### 5. Data Protection and Confidentiality
In this study, personal and personal data are collected for our research. The use of personal or subject-related information is governed by the European Union (EU) General Data Protection Regulation (GDPR) and will be treated in accordance with the GDPR. This means that you can view, correct, restrict processing, and delete the data collected in this study. Only with your agreement, we will log your input and manually record notes in the study. We plan to publish the results of this and other research studies in academic articles or other media. Your data will not be retained for longer than necessary or until you contact researchers to have your data destroyed or deleted. Access to the raw data, transcribed interviews, and observation protocols of the study is encrypted, password-protected and only accessible to the authors, colleagues and researchers collaborating on this research. Other members and administrators of our institution do not have access to your data. When publishing, the data will be anonymized using code numbers and published in aggregated form, so that without information from the researchers no conclusions can be drawn about individual persons. Any interview content or direct quotations from the interview, that are made available through academic publications or other academic outlets will also be anonymized using code numbers. Contact details (e.g. e-mails) will not be passed on to third parties, but may be used by the researchers to contact participants, trace infection chains, or to send you further details of the study. According to the GDPR, the researchers will inform the participants using their contact details if a confidential data breach has been detected.

#### 6. Identification of Investigators
If you have any questions or concerns about the research, please feel free to contact:

**Researchers**
                
Amit Ephraim Sadhu (amit.sadhu@stud.fra-uas.de), Joseph Anthony (joseph.antony@stud.fra-uas.de), Ramya Sai Murali (ramya.sai-murali@stud.fra-uas.de)  

Frankfurt University of Applied Sciences

**Principal investigator**

Prof. Dr. Valentin Schwind (valentin.schwind@fra-uas.de)  
                
Frankfurt University of Applied Sciences  
Nibelungenplatz 1  
60318 Frankfurt am Main, Germany  
""")
    name = st.text_input("Your name")
    email = st.text_input("Your student email")
    agreed = st.checkbox("I have read and agree to all the statements above")

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