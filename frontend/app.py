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
            full_response = ""
            
            # Change mock response based on toggles
            if wizard_mode:
                simulated_backend_response = f"Wizard Mode Active: Let's fill out your application together. Step 1: Do you currently have a copy of your old ID?"
            elif eli5_mode:
                simulated_backend_response = f"Simple Explanation: To get this done, you just need to bring your birth certificate and a photo to the office! It's very easy."
            else:
                simulated_backend_response = f"This is a placeholder response for your question: '{prompt}'. Once we connect the FastAPI backend, I will retrieve the official procedure here."
            
            for chunk in simulated_backend_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            final_output = f"{full_response}\n\n"
            
            # Add TTS placeholder
            final_output += """<div class='tts-button'>▶ Play Audio (Text-to-Speech)</div>"""
            
            if not eli5_mode and not wizard_mode:
                final_output += """<div class="citation-box"><b>Sources:</b><br>1. Aadhaar Handbook 2026 (Page 12)<br>2. IT Rules 2026 (Section 3)</div>"""
                
            message_placeholder.markdown(final_output, unsafe_allow_html=True)
            
        st.session_state.messages.append({"role": "assistant", "content": final_output})

if __name__ == "__main__":
    main()
