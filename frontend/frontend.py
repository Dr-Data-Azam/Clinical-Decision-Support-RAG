import streamlit as st
import requests
import os

# --- Final Configuration ---
# This code now ONLY uses an environment variable to find the backend.
# This is the standard practice for cloud deployments.
# For local testing with docker-compose, the 'docker-compose.yml' can set this.
# For Azure, the 'az containerapp' command sets this.
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/bot")


st.set_page_config(
    page_title="Heart Failure CDSS",
    layout="centered",
    initial_sidebar_state="expanded"
)
st.title("Heart Failure Management CDSS - 2022 AHA/ACC/HFSA")
# st.info(f"Frontend is configured to connect to the backend at: {BACKEND_URL}")


# --- The rest of your Streamlit app code remains the same ---
# (Initialize chat history, display messages, etc.)

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    with st.spinner("Processing and generating response..."):
        try:
            payload = {"message": user_input}
            response = requests.post(BACKEND_URL, json=payload)
            response.raise_for_status()
            bot_response_text = response.json()["output"]
            with st.chat_message('assistant'):
                st.markdown(bot_response_text)
            st.session_state['message_history'].append({'role': 'assistant', 'content': bot_response_text})
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to the backend. Details: {e}")
        except KeyError:
            st.error("Error: Received an unexpected format from the backend.")