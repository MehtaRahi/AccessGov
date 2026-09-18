import streamlit as st
import time

st.set_page_config(
    page_title="AccessGov - AI Assistive Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
    }
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

def main():
    st.title("AccessGov")
    st.subheader("Your AI-Powered Guide to Government Services")
    
    # --- SIDEBAR: Accessibility & Features ---
    with st.sidebar:
        st.header("Settings & Accessibility")
        st.selectbox("Text Size", ["Normal", "Large", "Extra Large"])
        st.toggle("High Contrast Mode")
        
        st.divider()
        
        st.header("Response Modes")
        eli5_mode = st.toggle("Explain Like I'm 5 (Simplify Jargon)")
        wizard_mode = st.toggle("Interactive Form-Filler Wizard")
        
        st.divider()
        st.caption("AccessGov is designed to simplify complex bureaucratic procedures and provide clear, authoritative answers.")

    # --- MAIN CONTENT AREA ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your AccessGov assistant. You can ask me how to apply for an Aadhaar card, what documents are needed for a PAN card, or questions about IT rules."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("E.g., What documents do I need to renew my passport?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            mode_str = "normal"
            if eli5_mode:
                mode_str = "eli5"
            elif wizard_mode:
                mode_str = "wizard"

            # Connect to backend
            try:
                import requests
                # Use docker network host 'backend' or fallback to localhost
                # Assuming this runs in Docker Compose, the backend is reachable at http://backend:8000
                api_url = "http://backend:8000/api/chat"
                
                response = requests.post(
                    api_url, 
                    json={"query": prompt, "mode": mode_str},
                    timeout=30
                )
                
                if response.status_code == 200:
                    backend_response = response.json().get("answer", "No answer received.")
                else:
                    backend_response = f"Backend Error: {response.status_code}"
            except requests.exceptions.RequestException as e:
                # Fallback to localhost if not in docker
                try:
                    api_url = "http://localhost:8001/api/chat"
                    response = requests.post(
                        api_url, 
                        json={"query": prompt, "mode": mode_str},
                        timeout=30
                    )
                    if response.status_code == 200:
                        backend_response = response.json().get("answer", "No answer received.")
                    else:
                        backend_response = f"Backend Error: {response.status_code}"
                except requests.exceptions.RequestException:
                    backend_response = f"Could not connect to the backend server. Is it running? Error details: {e}"

            # Simulate streaming the real response
            full_response = ""
            for chunk in backend_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            final_output = f"{full_response}\n\n"
            
            # Add TTS placeholder
            final_output += """<div class='tts-button'>▶ Play Audio (Text-to-Speech)</div>"""
            
            message_placeholder.markdown(final_output, unsafe_allow_html=True)
            
        st.session_state.messages.append({"role": "assistant", "content": final_output})

if __name__ == "__main__":
    main()
