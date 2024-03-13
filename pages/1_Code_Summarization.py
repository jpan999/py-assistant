import openai
import os
import streamlit as st
import anthropic
import yaml
import re
import warnings
from tempfile import NamedTemporaryFile
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from streamlit_feedback import streamlit_feedback
from langchain.callbacks.tracers.run_collector import RunCollectorCallbackHandler
from langchain.memory import StreamlitChatMessageHistory, ConversationBufferMemory
from langchain.schema.runnable import RunnableConfig
from langsmith import Client
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from src.components.infoLoader import InfoLoader
from src.components.vectorDB import VectorDB
from src.chatbot_utilities import LLMChatbot
warnings.filterwarnings("ignore")


def initialize_session_state():
    '''
    Handles initializing of session_state variables
    '''
    # Load config if not yet loaded
    if 'config' not in st.session_state:
        with open('config.yml', 'r') as file:
            st.session_state.config = yaml.safe_load(file)
    if 'conversation_memory' not in st.session_state:
    # Initialize a new conversation memory if it doesn't exist in the session
        st.session_state.conversation_memory = []

@st.cache_resource
def get_resources():
    '''
    Initializes the customer modules
    '''
    return InfoLoader(st.session_state.config), VectorDB(st.session_state.config)

# ----- Main Page -----

initialize_session_state()
loader, vector_DB = get_resources()

with st.sidebar:
    backend_model = st.selectbox(
        "Select the LLM you want to use",
        ("OpenAI gpt-3.5-turbo", "Anthropic claude-1.3"), 
        key="llm"
    )

    llm_api_key = st.text_input("OpenAI/Anthropic API Key", key="file_qa_api_key", type="password")
    if "chatbot" not in st.session_state or llm_api_key != st.session_state.chatbot.api_key:
        st.session_state.chatbot = LLMChatbot(llm_api_key)
    
    # use_secret_key = st.sidebar.toggle(label="Demo LangSmith API key", value=False)
    
st.title("Code Summarization with RAG")

model_encode = {"OpenAI gpt-3.5-turbo": "gpt-4-turbo", "Anthropic claude-1.3": "claude-1.3"}

model = model_encode[backend_model] # "claude-2" for Claude 2 model

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
    chatbot = st.session_state.chatbot
    if model != st.session_state.get("model", None):
        st.session_state["model"] = model
    chatbot.set_model(st.session_state["model"])

    for msg in chatbot.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not llm_api_key:
            st.info("Please add your API key to continue.")
            st.stop()
        st.chat_message("user").write(prompt)
        try:
            user_intent = chatbot.get_user_intent(prompt)
            if user_intent == "code summarization":
                with st.spinner('Generating answer...'):
                    reply = chatbot.generate_reply(prompt)
                    st.chat_message("assistant").write(reply)
            else:
                st.chat_message("assistant").write("I'm a Python assistant dedicated to code summarization. I'm not quite sure what you're asking for. Could you please provide more details about your request?")
        except openai.AuthenticationError:
            st.error("Please input a valid API key.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

else:
    # use file input
    langchain_api_key = st.sidebar.text_input(
        "👇 Add your LangSmith Key",
        value="",
        placeholder="Your LangSmith Key Here",
        label_visibility="collapsed",
        type="password"
    )

    if langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_PROJECT"] = "Streamlit Demo"

    if "last_run" not in st.session_state:
        st.session_state["last_run"] = "some_initial_value"
    if "trace_link" not in st.session_state:
        st.session_state.trace_link = None
    if "run_id" not in st.session_state:
        st.session_state.run_id = None
    if 'feedback_option' not in st.session_state:
        st.session_state.feedback_option = "faces"
    
    # Check if the LangSmith API key is provided
    if not langchain_api_key or langchain_api_key.strip() == "Your LangSmith Key Here":
        st.info("⚠️ Add your [LangSmith API key](https://python.langchain.com/docs/guides/langsmith/walkthrough) to continue.")
    else:
        client = Client(api_url=st.session_state.config["langchain_endpoint"], api_key=langchain_api_key)

    if st.sidebar.button("Clear message history"):
        print("Clearing message history")
        st.session_state.conversation_memory = []
        st.session_state.trace_link = None
        st.session_state.run_id = None
    
    run_collector = RunCollectorCallbackHandler()
    runnable_config = RunnableConfig(
        callbacks=[run_collector],
        tags=["Streamlit Chat"],
    )
    if st.session_state.trace_link:
        st.sidebar.markdown(
            f'<a href="{st.session_state.trace_link}" target="_blank"><button>Latest Trace: 🛠️</button></a>',
            unsafe_allow_html=True,
        )

    def _reset_feedback():
        st.session_state.feedback_update = None
        st.session_state.feedback = None
    
    uploaded_files = st.file_uploader(
            label = 'Upload code files for embedding', 
            help = 'Overwrites any existing files uploaded',
            type = ['py', 'txt'], 
            accept_multiple_files=True
            )
    
    if uploaded_files:
        if not llm_api_key:
            st.info("Please add your API key to continue.")
            st.stop()
        
        if model == "claude-1.3":
            openai_api_key = st.text_input(
                "Please input your OpenAI API key for embedding.",
                disabled=False,
                type="password"
            )
        else:
            openai_api_key = None  

        if st.button('Upload', type='primary'):
            with st.spinner('Uploading... (this may take a while)'):
                try:
                    st.write("Splitting documents...")
                    loader.get_chunks(uploaded_files)

                    if model == "claude-1.3":
                        # Check if the API key was provided
                        if not openai_api_key:
                            st.error("OpenAI API key is required for 'claude-1.3' model.")
                            st.stop()
                        vector_DB.create_embedding_function(openai_api_key)
                    else:
                        vector_DB.create_embedding_function(llm_api_key)

                    vector_DB.initialize_database(loader.document_chunks_full)
                    st.success('Embedding complete!')

                except Exception as e:
                    st.error(f'Error occurred: {e}')

    question = st.text_input(
        "Ask anything you want to know about the Python code",
        placeholder="I am reading code for a python application. Explain to me how it works.",
        disabled=not uploaded_files,
    )

    if st.button('Get Answer', type='primary') and question:
        vector_DB.create_llm(model, llm_api_key, 0.4)
        vector_DB.create_chain()

        result, source_docs = vector_DB.get_response(question, st.session_state.conversation_memory, runnable_config)
        # The run collector will store all the runs in order. We'll just take the root and then
        # reset the list for next interaction.
        run = run_collector.traced_runs[0]
        run_collector.traced_runs = []
        st.session_state.run_id = run.id
        wait_for_all_tracers()
        # Requires langsmith >= 0.0.19
        url = client.share_run(run.id)
        # url = client.read_run(run.id).url
        st.session_state.trace_link = url

        st.session_state.conversation_memory.append((question, result))

        st.info('Query Response:', icon='📕')
        st.write(result)
        st.write(' ')

        st.info('Source Documents:', icon='📚')
        for document in source_docs:
            st.markdown(document.page_content + '\n\n')
            st.write('-----------------------------------')

    has_chat_messages = len(st.session_state.get("conversation_memory", [])) > 0
    # Only show the feedback toggle if there are chat messages
    if has_chat_messages:
        st.session_state.feedback_option = (
            "thumbs" if st.toggle(label="`Thumbs` ⇄ `Faces`", value=False) else "faces"
        )
        feedback_option = st.session_state.feedback_option
    else:
        pass

    if st.session_state.get("run_id"):
        feedback = streamlit_feedback(
            feedback_type=feedback_option,  # Use the selected feedback option
            optional_text_label="[Optional] Please provide an explanation",  # Adding a label for optional text input
            key=f"feedback_{st.session_state.run_id}",
        )

        # Define score mappings for both "thumbs" and "faces" feedback systems
        score_mappings = {
            "thumbs": {"👍": 1, "👎": 0},
            "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
        }

        # Get the score mapping based on the selected feedback option
        scores = score_mappings[feedback_option]

        if feedback:
            # feedback = st.session_state.feedback_run
            # Get the score from the selected feedback option's score mapping
            score = scores.get(feedback["score"])

            if score is not None:
                # Formulate feedback type string incorporating the feedback option and score value
                feedback_type_str = f"{feedback_option} {feedback['score']}"

                # Record the feedback with the formulated feedback type string and optional comment
                feedback_record = client.create_feedback(
                    st.session_state.run_id,
                    feedback_type_str,  # Updated feedback type
                    score=score,
                    comment=feedback.get("text"),
                )
                st.session_state.feedback = {
                    "feedback_id": str(feedback_record.id),
                    "score": score,
                }
            else:
                st.warning("Invalid feedback score.")

    st.info('Chat History:', icon='💬')
    st.write(st.session_state.conversation_memory)