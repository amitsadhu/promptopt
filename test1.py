import os
import streamlit as st
from groq import Groq
from datetime import datetime
import hmac
from supabase import create_client, Client

# Supabase setup
supabase_url = st.secrets.get("SUPABASE_URL")
supabase_key = st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def save_comparison_to_supabase(comparison):
    try:
        data = {
            "timestamp": comparison["timestamp"],
            "original_prompt": comparison["original_prompt"],
            "optimized_prompt": comparison["optimized_prompt"],
            "user_preference": comparison["user_preference"]
        }
        supabase.table("prompt_comparisons").insert(data).execute()
    except Exception as e:
        st.error(f"Supabase insert error: {e}")

# Page configuration
st.set_page_config(
    page_title="Prompt Optimization Tool",
    page_icon="🔄",
    layout="wide"
)

def save_user_info_to_supabase(user_info):
    try:
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": user_info["name"],
            "email": user_info["email"],
            "agreed": user_info["agreed"]
        }
        supabase.table("user_info").insert(data).execute()
    except Exception as e:
        st.error(f"Supabase user info insert error: {e}")

if "user_info_submitted" not in st.session_state:
    st.session_state.user_info_submitted = False

if not st.session_state.user_info_submitted:
    st.title("Welcome to the Prompt Optimization Tool")
    st.markdown("""
    ### Terms and Conditions
    Please read and accept the following terms before using this application.
    - Your prompts and responses will be stored for research purposes.
    - Your name and email will be used to associate your data.
    - You may withdraw at any time by contacting the administrator.
    """)

    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    agreed = st.checkbox("I have read and agree to the terms and conditions.")

    if st.button("Submit"):
        if not name or not email or not agreed:
            st.warning("Please fill in all fields and agree to the terms.")
        else:
            user_info = {"name": name, "email": email, "agreed": agreed}
            save_user_info_to_supabase(user_info)
            st.session_state.user_info_submitted = True
            st.session_state.user_name = name
            st.session_state.user_email = email
            st.success("Thank you! You may now use the app.")
            st.rerun()
    st.stop()

# Authentication function
def check_password():
    """Returns `True` if the user has entered the correct password."""
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets.get("PASSWORD")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.title("Prompt Optimization Tool")
    st.subheader("Please enter the password to access this application")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )

    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")

    return False

# Check password before showing the main app
if not check_password():
    st.stop()

# Get API key from secrets
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except KeyError as e:
    st.error(f"Missing API key in secrets.toml: {str(e)}")
    st.stop()

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []

# Sidebar for configuration
with st.sidebar:
    st.title("Configuration")

    # Fixed models
    response_model = "llama-3.1-8b-instant"
    optimization_model = "llama-3.3-70b-versatile"

    # Display the fixed models as information
    st.subheader("Model Information")
    st.info(f"Optimization Model: {optimization_model}")
    st.info(f"Response Model: {response_model}")

    # API Status
    st.subheader("API Status")
    st.success("✅ Groq API Key Loaded")

    # System prompt for optimization
    st.subheader("Optimization Settings")
    optimization_prompt = st.text_area(
        "Optimization System Prompt",
        """You are an expert prompt engineer. Your sole task is to analyze and optimize the provided prompt without executing it or providing answers to its content. **Instructions:** 
        1. Analyze the input prompt for clarity, specificity, and effectiveness
        2. Identify areas for improvement such as:
        - Ambiguous language or unclear instructions
        - Missing context or background information
        - Vague output requirements or format specifications
        - Incomplete task parameters or constraints
        3. Rewrite the prompt to be more precise, actionable, and likely to produce the desired results
        4. Ensure the optimized version includes:
        - Clear, specific instructions
        - Defined output format and structure
        - Relevant context and constraints
        - Appropriate tone and style guidance if needed
        NEVER RESPOND TO THE PROMPT CONTENT OR EXECUTE ANY TASKS. ONLY FOCUS ON OPTIMIZING THE PROMPT ITSELF.""",
    )

# Main content
st.title("Prompt Optimization Tool")
st.caption("Compare responses from original vs. optimized prompts using Groq models")

# Input area
user_prompt = st.text_area("Enter your prompt:", height=150)

# Function to call Groq API for prompt optimization
def optimize_prompt(prompt, system_prompt):
    try:
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model=optimization_model,
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

# Function to call Groq API for responses
def get_groq_response(prompt, model):
    try:
        st.info(f"Calling Groq API with model: {model}")
        client = Groq(api_key=groq_api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )
        
        st.success("✅ Groq API call successful")
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"❌ Error with Groq response API: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        return None

# Process button
if st.button("Process Prompt"):
    if not user_prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Processing..."):
            # Step 1: Optimize the prompt using Groq
            st.info("Step 1: Optimizing prompt with Groq...")
            optimized_prompt = optimize_prompt(user_prompt, optimization_prompt)

            if optimized_prompt:
                st.success("✅ Prompt optimization complete")
                st.info("Step 2: Getting responses from Groq...")
                
                # Step 2: Get responses from Groq for both prompts
                original_response = get_groq_response(user_prompt, response_model)
                
                if original_response:
                    optimized_response = get_groq_response(optimized_prompt, response_model)
                    
                    if optimized_response:
                        # Store the results
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        comparison = {
                            "timestamp": timestamp,
                            "original_prompt": user_prompt,
                            "optimized_prompt": optimized_prompt,
                            "original_response": original_response,
                            "optimized_response": optimized_response,
                            "user_preference": None
                        }
                        st.session_state.comparison_results.append(comparison)
                        st.success("🎉 Processing complete!")
                    else:
                        st.error("Failed to get optimized response")
                else:
                    st.error("Failed to get original response")
            else:
                st.error("Failed to optimize prompt")

# Display the most recent comparison
if st.session_state.comparison_results:
    latest = st.session_state.comparison_results[-1]

    st.subheader("Comparison Results")

    col1, col2 = st.columns(2)

    with col1:
        st.text_area("Response 1",latest["original_response"], height=300, disabled=True)
        if st.button("Prefer Response 1"):
            st.session_state.comparison_results[-1]["user_preference"] = "original"
            save_comparison_to_supabase(st.session_state.comparison_results[-1])
            st.success("Preference saved!")

    with col2:
        st.text_area("Response 2",latest["optimized_response"], height=300, disabled=True)
        if st.button("Prefer Response 2"):
            st.session_state.comparison_results[-1]["user_preference"] = "optimized"
            save_comparison_to_supabase(st.session_state.comparison_results[-1])
            st.success("Preference saved!")

# History section
if st.session_state.comparison_results:
    st.subheader("History")
    for i, result in enumerate(reversed(st.session_state.comparison_results[:-1])):
        with st.expander(f"Comparison {len(st.session_state.comparison_results) - i - 1}: {result['timestamp']}"):
            st.markdown(f"**Original Prompt:** {result['original_prompt']}")
            #st.markdown(f"**Optimized Prompt:** {result['optimized_prompt']}")
            st.markdown(f"**User Preference:** {result['user_preference'] or 'Not selected'}")

