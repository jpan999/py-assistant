from openai import OpenAI
import anthropic
import streamlit as st
import re
import warnings
warnings.filterwarnings("ignore")

with st.sidebar:
    api_key = st.text_input("OpenAI/Claude API Key", key="chatbot_api_key", type="password")
    #"[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

st.title("💬 Py Assistant")
st.caption("🚀 Talk your way through your Python code!")

# Model binary mapping
model_encode = {"✨ GPT-3.5": 0, "♾️ Claude": 1}

# Model selection mapping
model_mapping = {0: "gpt-3.5-turbo", 1: "claude-v1"}

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

INITIAL_MESSAGE = [
    {"role": "user", "content": "Hi!"},
    {
        "role": "assistant",
        "content": "Hey there, I'm your Python-speaking coding assistant, ready to answer your questions regarding Python code!💻",
    },
]

# Function to send a message to the model asking for intent classification
def get_intent_classification(prompt, client):
    # Construct a prompt for the model to classify the intent
    classification_prompt = f"Classify the following user intent: '{prompt}'. Is the user asking for code generation, code summarization, or code translation? "

    # Send the prompt to the model
    if st.session_state["model"] == "gpt-3.5-turbo":

        response = client.chat.completions.create(model=st.session_state["model"], messages=[
            {"role": "system", "content": "I am a coding assistant capable of classifying user intent."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": classification_prompt},
        ])
        intent = response.choices[0].message.content
    else:

        response = client.completions.create(
            prompt=f"""{anthropic.HUMAN_PROMPT} {classification_prompt}{anthropic.AI_PROMPT}""",
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model="claude-v1",  # "claude-2" for Claude 2 model
            max_tokens_to_sample=300,
        )
        intent = response.completion
    
    if "code generation" in intent.lower():
        intent = "code generation"
    elif "code summarization" in intent.lower():
        intent = "code summarization"
    elif "code translation" in intent.lower(): 
        intent = "code translation"
    else:
        intent = "Please specify your task as one of the categories: code generation, code summarization, or code translation."
    # The model's response should contain the classification
    return intent

# for openai
if model_encode[model] == 0:
    if "messages" not in st.session_state:
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

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        user_intent = get_intent_classification(prompt, client)
        st.session_state.messages.append({"role": "assistant", "content": f"Based on the input, the user intent is: {user_intent} Please proceed with the identified task."})
        st.chat_message("assistant").write(f"Based on your input, I identified your intent as: \n {user_intent}. Now I will proceed with the identified task.")
                                         
        response = client.chat.completions.create(model=st.session_state["model"], messages=st.session_state.messages)
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
        # Side note: example of st.session_state.messages: 
        #[{'role': 'user', 'content': 'Hi!'}, {'role': 'assistant', 'content': "Hey there, I'm your 
        #Python-speaking coding assistant, ready to answer your questions regarding Python code!💻"}, 
        #{'role': 'user', 'content': 'tell me your name'}, {'role': 'user', 'content': 'tell me your name'}]
    
else:
# for anthropic
    if "messages" not in st.session_state:
        st.session_state["messages"] = INITIAL_MESSAGE

    if "model" not in st.session_state:
        st.session_state["model"] = model

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not api_key:
            st.info("Please add your Claude API key to continue.")
            st.stop()
        
        client = anthropic.Client(api_key=api_key)

        st.session_state.messages.append({"role": "user", "content": prompt})

        st.chat_message("user").write(prompt)

        user_intent = get_intent_classification(prompt, client)
        st.chat_message("assistant").write(f"Based on your input, I identified your intent as: \n {user_intent}. Now I will proceed with the identified task.")

        chat_prompt = f"""{anthropic.HUMAN_PROMPT} Here's the user input: {prompt} The identified task for the input is {user_intent} 
        Please proceed with the identified task. {anthropic.AI_PROMPT}"""
        
        response = client.completions.create(
            prompt=chat_prompt,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model="claude-v1",  # "claude-2" for Claude 2 model
            max_tokens_to_sample=300,
        )

        msg = response.completion
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)