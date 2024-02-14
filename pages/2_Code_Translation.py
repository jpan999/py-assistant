import streamlit as st
from openai import OpenAI
import re
import warnings
warnings.filterwarnings("ignore")


with st.sidebar:
    api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

    target_language = st.selectbox(
        "Select target language for translation:",
        ("Java", "C++", "JavaScript", "Go"),  # Add or remove languages as needed
        key="target_language"
    )

st.title("Code Translation")

model = "gpt-3.5-turbo" # use gpt-3.5-turbo

# a radio to select file or manual prompt
input_mode = st.radio(
    "",
    options=["✨ chat", "♾️ file"],
    index=0,
    horizontal=True,
)

# input mode binary mapping
mode_encode = {"✨ chat": 0, "♾️ file": 1}


if mode_encode[input_mode] == 0:
    
    # use chat mode
    INITIAL_MESSAGE = [
        {"role": "user", "content": "Hi!"},
        {
            "role": "assistant",
            "content": "Hey there, I'm your Python-speaking coding assistant, ready to translate your Python code into any popular language!",
        },
    ]

    st.session_state["messages"] = INITIAL_MESSAGE

    if "model" not in st.session_state:
        st.session_state["model"] = model

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()
        
        client = OpenAI(api_key=api_key)

        # append system instructions
        st.session_state.messages.append({"role": "system", "content": f"I am a coding assistant capable of translating Python code into {target_language}."})
        # append user prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Step 1: Pre-Translation Assessment
        suitability_prompt = f"Check if the following code is suitable for translation to {target_language}: {prompt}. Specifically, please check for the code structure and dependencies. If suitable, please return 'suitable' as the answer. Else, please return an error message that contains 'not suitable' and states why it's not suitable."
        response = client.chat.completions.create(model=st.session_state["model"], messages=[
            {"role": "system", "content": "I am a coding assistant capable of translating Python code into other coding languages."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": suitability_prompt},
        ])
        suitability_response = response.choices[0].message.content

        if "not suitable" in suitability_response.lower():
            error_msg = "\n The provided code may not be suitable for translation to the selected language. Please check your code and try again."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.chat_message("assistant").write(suitability_response + error_msg)
        
        else:
            # Step 2: Append assistant message
            st.session_state.messages.append({"role": "assistant", "content": f"Please translate the user-input python code into {target_language}. The translated code should be functional and as concise as possible."})
            with st.spinner('Generating answer...'):
                response = client.chat.completions.create(model=st.session_state["model"], messages=st.session_state.messages)
                msg = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)

else:
    # use file input
    uploaded_file = st.file_uploader("Upload a Python file", type=("txt", "py"))
    if uploaded_file:
        if "last_uploaded_file" not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.last_uploaded_file = uploaded_file.name 
            # Reset messages for new file
            st.session_state.messages = []

    if uploaded_file and not api_key:
        st.info("Please add your OpenAI API key to continue.")

    if uploaded_file and api_key:
        code_file = uploaded_file.read().decode()

        client = OpenAI(api_key=api_key)
        # append system instructions
        st.session_state.messages.append({"role": "system", "content": f"I am a coding assistant capable of translating Python code into {target_language}."})
        # append user prompt
        st.session_state.messages.append({"role": "user", "content": code_file})

        # Step 1: Pre-Translation Assessment
        suitability_prompt = f"Check if the above user-input Python code is suitable for translation to {target_language}. Specifically, please check for the code structure and dependencies. If suitable, please return 'suitable' as the answer. Else, please return an error message that contains 'not suitable' and states why it's not suitable."
        response = client.chat.completions.create(model=st.session_state["model"], messages=[
            {"role": "system", "content": "I am a coding assistant capable of translating Python code into other coding languages."},
            {"role": "user", "content": code_file},
            {"role": "assistant", "content": suitability_prompt},
        ])
        suitability_response = response.choices[0].message.content

        if "not suitable" in suitability_response.lower():
            error_msg = "\n Please check your code and try again."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.chat_message("assistant").write(suitability_response + error_msg)
        
        # Step 2: Generate translation if pre-check passes
        else:
            # append assistant message
            st.session_state.messages.append({"role": "assistant", "content": f"Please translate the user-input python code into {target_language}. The translated code should be functional and as concise as possible."})
            
            with st.spinner('Generating answer...'):
                response = client.chat.completions.create(model=st.session_state["model"], messages=st.session_state.messages)
                code_generated = response.choices[0].message.content
            st.write("### Translated code:")
            st.markdown(code_generated)
            st.download_button(
                label="Download Code",
                data=code_generated,
                file_name="generated_code.java",
                mime="text/plain"
            )
