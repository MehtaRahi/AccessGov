import streamlit as st
import time
import requests
import html
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="AccessGov - AI Assistive Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    .citation-box {
        background-color: #2e3035;
        color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        border-left: 5px solid #0056b3;
        margin-top: 15px;
    }
    .tts-button {
        font-size: 12px;
        color: #007bff;
        cursor: pointer;
        padding-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# URL logic for backend
BACKEND_URL = "http://backend:8000"

def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AccessGov assistant. How can I help you today?"}]
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "name" not in st.session_state:
        st.session_state.name = None

def reset_chat():
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AccessGov assistant. How can I help you today?"}]

def login_register_ui():
    st.sidebar.header("Account")
    if st.session_state.token:
        st.sidebar.write(f"Logged in as **{st.session_state.name}**")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user_id = None
            st.session_state.name = None
            reset_chat()
            st.rerun()
    else:
        tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                try:
                    res = requests.post(f"{BACKEND_URL}/api/auth/login", json={"email": email, "password": password})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user_id = data["user_id"]
                        st.session_state.name = data["name"]
                        st.success("Logged in!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except Exception as e:
                    st.error(f"Error: {e}")
        with tab2:
            reg_name = st.text_input("Name", key="reg_name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Register", use_container_width=True):
                try:
                    res = requests.post(f"{BACKEND_URL}/api/auth/register", json={"email": reg_email, "password": reg_password, "name": reg_name})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user_id = data["user_id"]
                        st.session_state.name = data["name"]
                        st.success("Registered and logged in!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Registration failed"))
                except Exception as e:
                    st.error(f"Error: {e}")

def main():
    init_session()
    
    st.title("AccessGov")
    st.subheader("Your AI-Powered Guide to Government Services")
    
    # --- SIDEBAR: Cleaner UI ---
    with st.sidebar:
        login_register_ui()
        st.divider()
        st.header("Settings & Accessibility")
        st.selectbox("Text Size", ["Normal", "Large", "Extra Large"])
        st.toggle("High Contrast Mode")
        dyslexia_font = st.toggle("Dyslexia-Friendly Font")
        
        st.divider()
        st.write("🎙️ **Voice Input**")
        voice_prompt = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
        
        st.divider()
        if st.button("New Chat", use_container_width=True):
            reset_chat()
            st.rerun()

    if dyslexia_font:
        st.markdown("""
        <style>
        * { font-family: 'Comic Sans MS', 'OpenDyslexic', cursive, sans-serif !important; }
        </style>
        """, unsafe_allow_html=True)

    def render_tts(text):
        escaped_text = html.escape(text).replace('\\n', ' ').replace('\\r', '').replace("'", "\\'")
        components.html(f"""
            <button onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('{escaped_text}'))" 
                    style="background:none; border:none; color:#007bff; cursor:pointer; font-size:14px; padding:0; font-family:sans-serif;">
                ▶ Play Audio (Text-to-Speech)
            </button>
        """, height=30)

    # --- MAIN CONTENT AREA ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
            if message["role"] == "assistant":
                render_tts(message["content"])

    text_prompt = st.chat_input("E.g., What documents do I need to renew my passport?")
    prompt = text_prompt or voice_prompt

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Extract last 4 messages (excluding the very first greeting and the current prompt)
            history = []
            if len(st.session_state.messages) > 2:
                history = st.session_state.messages[1:-1][-4:]

            payload = {
                "query": prompt, 
                "mode": "normal", 
                "chat_history": history
            }
            if st.session_state.user_id:
                payload["user_id"] = st.session_state.user_id

            # Connect to backend
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/chat", 
                    json=payload,
                    timeout=180
                )
                
                if response.status_code == 200:
                    backend_response = response.json().get("answer", "No answer received.")
                else:
                    backend_response = f"Backend Error: {response.status_code}"
            except Exception as e:
                backend_response = f"Could not connect to the backend server. Error details: {e}"

            # Simulate streaming the real response
            full_response = ""
            for chunk in backend_response.split():
                full_response += chunk + " "
                time.sleep(0.02)
                message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            final_output = f"{full_response}\n\n"
            message_placeholder.markdown(final_output, unsafe_allow_html=True)
            render_tts(final_output)
            
        st.session_state.messages.append({"role": "assistant", "content": final_output})

if __name__ == "__main__":
    main()
