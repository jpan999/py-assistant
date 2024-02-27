from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.callbacks import get_openai_callback


class VectorDB():
    def __init__(self, config):
        self.config = config
        self.db_option = config['embedding_options']['db_option']
        self.document_names = None

    def create_embedding_function(self, openai_api_key : str):
        self.embedding_function = OpenAIEmbeddings(
            model=self.config['embedding_options']['model'],
            show_progress_bar=True,
            openai_api_key = openai_api_key) 
    
    def initialize_database(self, document_chunks : list):
        # Track tokem usage
        if self.db_option == 'chroma':
            self.vector_db = Chroma.from_documents(document_chunks, self.embedding_function)

    def create_llm(self, model: str, openai_api_key : str, temperature : int):
        # Instantiate the llm object 
        self.llm = ChatOpenAI(
                        model_name=model,
                        temperature=temperature,
                        api_key=openai_api_key
                        )
        

    def create_chain(self):
        if self.config['prompt_mode'] == 'Restricted':
            # Build prompt template
            template = """Use the following pieces of context to answer the question at the end. \
            If you don't know the answer, just say that you don't know, don't try to make up an answer. \
            Keep the answer as concise as possible. 
            Context: {context}
            Question: {question}
            Helpful Answer:"""
            qa_chain_prompt = PromptTemplate.from_template(template)
        elif self.config['prompt_mode'] == 'Unrestricted':
            # Build prompt template
            template = """Use the following pieces of context to answer the question at the end. \
            If you don't know the answer, you may make inferences, but make it clear in your answer. \
            Elaborate on your answer.
            Context: {context}
            Question: {question}
            Helpful Answer:"""
            qa_chain_prompt = PromptTemplate.from_template(template)

        # Build QuestionAnswer chain
        self.qa_chain = RetrievalQA.from_chain_type(
            self.llm,
            retriever=self.vector_db.as_retriever(
                search_type="similarity", # mmr, similarity_score_threshold, similarity
                search_kwargs = {
                        "k": 4}                  #k: Amount of documents to return (Default: 4)
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": qa_chain_prompt}
        )
    
    def get_response(self, user_input : str):
        # Query and Response
        with get_openai_callback() as cb:
            result = self.qa_chain({"query": user_input})
        return result