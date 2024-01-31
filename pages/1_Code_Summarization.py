import streamlit as st
import anthropic
import re
import warnings
warnings.filterwarnings("ignore")


with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password")
    
st.title("Code Summarization with Anthropic")

model = "claude-v1" # "claude-2" for Claude 2 model

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
            "content": "Hey there, I'm your Python-speaking coding assistant, ready to answer your questions regarding Python code!💻",
        },
    ]

    if "messages" not in st.session_state:
        st.session_state["messages"] = INITIAL_MESSAGE

    if "model" not in st.session_state:
        st.session_state["model"] = model

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not anthropic_api_key:
            st.info("Please add your Claude API key to continue.")
            st.stop()
        
        client = anthropic.Client(api_key=anthropic_api_key)

        st.session_state.messages.append({"role": "user", "content": prompt})

        st.chat_message("user").write(prompt)
        
        response = client.completions.create(
            prompt=f"""{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}""",
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model=model,  
            max_tokens_to_sample=300,
        )

        msg = response.completion
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

else:
    # use file input
    uploaded_file = st.file_uploader("Upload a Python file", type=("txt", "py"))
    question = st.text_input(
        "Ask anything you want to know about the Python code",
        placeholder="I am reading code for a python application. Explain to me how it works.",
        disabled=not uploaded_file,
    )

    if uploaded_file and question and not anthropic_api_key:
        st.info("Please add your Anthropic API key to continue.")

    if uploaded_file and question and anthropic_api_key:
        code_file = uploaded_file.read().decode()
        prompt = f"""{anthropic.HUMAN_PROMPT} Here's a python file:\n\n<article>
        {code_file}\n\n</article>\n\n{question}{anthropic.AI_PROMPT}"""

        client = anthropic.Client(api_key=anthropic_api_key)
        response = client.completions.create(
            prompt=prompt,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model="claude-v1",  # "claude-2" for Claude 2 model
            max_tokens_to_sample=100,
        )
        st.write("### Answer")
        st.write(response.completion)
