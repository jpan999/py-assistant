import openai
from openai import OpenAI
import streamlit as st
import anthropic
import yaml
import re
import warnings
from tempfile import NamedTemporaryFile
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from src.components.infoLoader import Gen_info_loader
from src.components.vectorDB import VectorDB_gen
from src.chatbot_utilities import LLMChatbot
from crawl.extract_code_from_urls import get_code_strings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
warnings.filterwarnings("ignore")


# Note: need to install:
# pip install google-cloud-aiplatform==1.36.2 langchain==0.0.332  faiss-cpu==1.7.4 nbformat

# def initialize_session_state():
#     '''
#     Handles initializing of session_state variables
#     '''
#     # Load config if not yet loaded
#     if 'config' not in st.session_state:
#         with open('config.yml', 'r') as file:
#             st.session_state.config = yaml.safe_load(file)
#     if 'conversation_memory' not in st.session_state:
#     # Initialize a new conversation memory if it doesn't exist in the session
#         st.session_state.conversation_memory = []

# @st.cache_resource
# def get_resources():
#     '''
#     Initializes the customer modules
#     '''
#     return Gen_info_loader(), VectorDB_gen(st.session_state.config)

###### Main Page #####
with st.sidebar:
    api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    if "chatbot" not in st.session_state or api_key != st.session_state.chatbot.api_key:
        st.session_state.chatbot = LLMChatbot(api_key)

st.title("Code Generation")

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

    chatbot = st.session_state.chatbot

    if "model" != st.session_state.get("model", None):
        st.session_state["model"] = model
    chatbot.set_model(st.session_state["model"])

    for msg in chatbot.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()
        
        st.session_state.chatbot = LLMChatbot(api_key)

        # append system instructions
        chatbot.add_message("system", f"I am a coding assistant capable of generating Python code under your instruction.")

        # append user prompt
        st.chat_message("user").write(prompt)

        try:

            # Step 1: Pre-Generation Assessment
            suitable, suitability_response = chatbot.check_gen_suitability(prompt)
            if suitable == 0:
                error_msg = "\n The provided code may not be suitable for Python code generation. Please check your prompt and try again."
                chatbot.add_message("assistant", suitability_response + error_msg)
                st.chat_message("assistant").write(suitability_response + error_msg)
            
            else:

                # Step 2: Append assistant message
                with st.spinner('Generating answer...'):

                    # result = VectorDB_gen.get_response(prompt)
                    # print("result")
                    # st.chat_message("assistant").write(result['source_documents'])
                    # chatbot.add_message("assistant", result)
                    # st.session_state.conversation_memory.append((prompt, result['answer']))
                    # st.write(st.session_state.conversation_memory)

                    reply = chatbot.generate_pycode(prompt)
                    st.chat_message("assistant").write(reply)

        except openai.AuthenticationError:
            st.error("Please input a valid API key")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

else:

    # # load rag instruction
    # st.write("loading RAG functionality")

    ########### Prepare for RAG  #############
    # initialize_session_state()
    # loader, VectorDB_gen = get_resources()

    # # get code strings
    # code_strings = get_code_strings()
    # loader.chunk_code_strings(code_strings)
    # print("chunk_code_strings done")

    # # vector_db embedding
    # VectorDB_gen.create_embedding_function(api_key)
    # print("create_embedding_func done")

    # # create index from embedded code chunks
    # VectorDB_gen.initialize_database(loader.code_string_full)
    # print("initialize_database done")

    # st.write("RAG loading complete!")
    ##########################################

    # use file input
    uploaded_file = st.file_uploader("Upload a .txt file", type="txt")
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
        st.session_state.messages.append({"role": "system", "content": f"Hey there, I'm your Python-speaking coding assistant, ready to design Python code under your instruction!"})
        # append user prompt
        st.session_state.messages.append({"role": "user", "content": code_file})

        # Step 1: Pre-Gen Assessment
        suitability_prompt = f"Check if the following code is suitable for code generation. Specifically, please check if the prompt can be translated into Python programming language. If suitable, please return 'suitable' as the answer. Else, please return an error message that contains 'not suitable' and states why it's not suitable."
        response = client.chat.completions.create(model=st.session_state["model"], messages=[
            {"role": "system", "content": "I am a coding assistant capable of translating your human language into Python functions."},
            {"role": "user", "content": code_file},
            {"role": "assistant", "content": suitability_prompt},
        ])
        suitability_response = response.choices[0].message.content

        if "not suitable" in suitability_response.lower():
            error_msg = "\n The provided code may not be suitable for Python code generation. Please check your prompt and try again."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.chat_message("assistant").write(suitability_response + error_msg)
        
        # Step 2: Generate translation if pre-check passes
        else:

            # VectorDB_gen.create_llm(model, api_key, 0.4)
            # print("create_llm done")

            # VectorDB_gen.create_chain()
            # print("create_chain done")

            # append assistant message
            st.session_state.messages.append({"role": "assistant", "content": f"Please translate the user-input human language into Python code. The translated code should be functional and as concise as possible."})
            
            with st.spinner('Generating answer...'):
                # result = VectorDB_gen.get_response(code_file)
                
                response = client.chat.completions.create(model=st.session_state["model"], messages=st.session_state.messages)
                code_generated = response.choices[0].message.content
            st.write("### Generated code:")
            print(code_generated)
            st.markdown(code_generated)

            # st.write("### Suggested contents:")
            # for document in result['source_documents']:
            #     st.markdown(document.page_content + '\n\n')
            #     st.write('-----------------------------------')  
                        
            st.download_button(
                label="Download Code",
                data=code_generated,
                file_name="generated_code.java",
                mime="text/plain"
            )
