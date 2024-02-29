import streamlit as st
import anthropic
import yaml
import re
import warnings
from tempfile import NamedTemporaryFile
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from src.components.infoLoader import InfoLoader
from src.components.vectorDB import VectorDB
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
    
st.title("Code Summarization with RAG")

model_encode = {"OpenAI gpt-3.5-turbo": "gpt-3.5-turbo", "Anthropic claude-1.3": "claude-1.3"}

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
    INITIAL_MESSAGE = [
        {"role": "user", "content": "Hi!"},
        {
            "role": "assistant",
            "content": "Hey there, I'm your Python-speaking coding assistant, ready to answer your questions regarding Python code!💻",
        },
    ]

    st.session_state["messages"] = INITIAL_MESSAGE

    if "model" not in st.session_state:
        st.session_state["model"] = model

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not llm_api_key:
            st.info("Please add your Claude API key to continue.")
            st.stop()
        
        client = anthropic.Client(api_key=llm_api_key)

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

        result = vector_DB.get_response(question, st.session_state.conversation_memory)
        st.session_state.conversation_memory.append((question, result['answer']))
        st.info('Query Response:', icon='📕')
        st.write(result['answer'])
        st.write(' ')
        st.info('Source Documents:', icon='📚')
        for document in result['source_documents']:
            st.markdown(document.page_content + '\n\n')
            st.write('-----------------------------------')
        st.info('Chat History:', icon='💬')
        st.write(st.session_state.conversation_memory)