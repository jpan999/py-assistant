import openai
from openai import OpenAI
import anthropic
import streamlit as st
from src.chatbot_utilities import LLMChatbot
import re
import warnings
warnings.filterwarnings("ignore")

with st.sidebar:
    api_key = st.text_input("OpenAI/Claude API Key", key="chatbot_api_key", type="password")
    if "chatbot" not in st.session_state or api_key != st.session_state.chatbot.api_key:
        st.session_state.chatbot = LLMChatbot(api_key)

st.title("💬 Py Assistant")
st.caption("🚀 Talk your way through your Python code!")
chatbot = st.session_state.chatbot

# Model binary mapping
model_encode = {"✨ GPT-3.5": 0, "♾️ Claude": 1}

# Model selection mapping
model_mapping = {0: "gpt-3.5-turbo", 1: "claude-1.3"}

# Display the model selection radio button
model = st.radio(
    "",
    options=["✨ GPT-3.5", "♾️ Claude"],
    index=0,
    horizontal=True,
)

# Update the session state for the model if it changes
if model != st.session_state.get("model", None):
    st.session_state["model"] = model_mapping[model_encode[model]]
    print(model_mapping[model_encode[model]])
    chatbot.set_model(st.session_state["model"])

for msg in chatbot.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not api_key:
        st.info("Please add your API key to continue.")
        st.stop()

    st.chat_message("user").write(prompt)

    try:
            
        user_intent = chatbot.get_user_intent(prompt)
        if user_intent:
            st.chat_message("assistant").write(f"Based on your input, I identified your intent as: \n {user_intent}. Now I will proceed with the identified task.")

            reply = chatbot.generate_reply(prompt)
            st.chat_message("assistant").write(reply)
        else: 
            if chatbot.retrieve_beginner_status(prompt): # new to python
                st.chat_message("assistant").write("Welcome to Python!")
                reply = chatbot.generate_beginner_reply(prompt)
                st.chat_message("assistant").write(reply)
            else:
                st.chat_message("assistant").write("I'm not quite sure what you're asking for. Could you please clarify whether you need help with code generation, code summarization, or code translation? Alternatively, you can provide more details about your request.")
    except openai.AuthenticationError:
        st.error("Please input a valid API key.")
    except Exception as e:
        # This block catches other exceptions and displays a generic error message
        st.error(f"An error occurred: {str(e)}")