import streamlit as st
import anthropic

with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password")
    

st.title("Code Summarization with Anthropic")
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
