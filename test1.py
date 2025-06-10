import os
import streamlit as st
from groq import Groq
from datetime import datetime
import hmac

# Page configuration
st.set_page_config(
    page_title="Prompt Optimization Tool",
    page_icon="🔄",
    layout="wide"
)

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
        "You are an expert prompt engineer. Your task is to optimize the user's prompt to get the best possible response from an AI model. Improve clarity, specificity, and structure while maintaining the original intent. Return ONLY the optimized prompt with no explanations."
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
        st.markdown("### Original Prompt")
        st.text_area("Original", latest["original_prompt"], height=100, disabled=True)
        st.markdown("### Response")
        st.text_area("Original Response", latest["original_response"], height=300, disabled=True)
        if st.button("Prefer Original"):
            st.session_state.comparison_results[-1]["user_preference"] = "original"
            st.success("Preference saved!")

    with col2:
        st.markdown("### Optimized Prompt")
        st.text_area("Optimized", latest["optimized_prompt"], height=100, disabled=True)
        st.markdown("### Response")
        st.text_area("Optimized Response", latest["optimized_response"], height=300, disabled=True)
        if st.button("Prefer Optimized"):
            st.session_state.comparison_results[-1]["user_preference"] = "optimized"
            st.success("Preference saved!")

# History section
if st.session_state.comparison_results:
    st.subheader("History")
    for i, result in enumerate(reversed(st.session_state.comparison_results[:-1])):
        with st.expander(f"Comparison {len(st.session_state.comparison_results) - i - 1}: {result['timestamp']}"):
            st.markdown(f"**Original Prompt:** {result['original_prompt']}")
            st.markdown(f"**Optimized Prompt:** {result['optimized_prompt']}")
            st.markdown(f"**User Preference:** {result['user_preference'] or 'Not selected'}")

