from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
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

    def create_llm(self, model: str, llm_api_key : str, temperature : int):
        # Instantiate the llm object 
        if model == "gpt-3.5-turbo":
            self.llm = ChatOpenAI(
                            model_name=model,
                            temperature=temperature,
                            api_key=llm_api_key
                        )
        else:
            self.llm = ChatAnthropic(model_name=model,
                                     temperature=temperature,
                                      anthropic_api_key=llm_api_key )
        

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
            template = """Use the following pieces of chat history and context to answer the question at the end. \
            If you don't know the answer, you may make inferences, but make it clear in your answer. \
            Elaborate on your answer.
            Chat History: {chat_history}
            Context: {context}
            Question: {question}
            Helpful Answer:"""
            qa_chain_prompt = PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)
        # Build QuestionAnswer chain
        # self.qa_chain = RetrievalQA.from_chain_type(
        #     self.llm,
        #     retriever=self.vector_db.as_retriever(
        #         search_type="similarity", # mmr, similarity_score_threshold, similarity
        #         search_kwargs = {
        #                 "k": 4} #k: Amount of documents to return (Default: 4)
        #     ),
        #     return_source_documents=True,
        #     chain_type_kwargs={"prompt": qa_chain_prompt}
        # )

        memory = ConversationBufferMemory(
                        llm=self.llm, memory_key="chat_history", output_key="answer", return_messages=True
                )
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, 
            retriever=self.vector_db.as_retriever(
                search_type="similarity",  
                search_kwargs={"k": 4} 
            ),
            verbose=True,
            chain_type="stuff",
            get_chat_history=lambda h : h,
            combine_docs_chain_kwargs={'prompt': qa_chain_prompt},
            memory = memory,
            return_source_documents=True
        )
    
    def get_response(self, user_input : str, chat_history: list):
        # Query and Response
        with get_openai_callback() as cb:
            result = self.qa_chain({"question": user_input, "chat_history": chat_history})
        return result