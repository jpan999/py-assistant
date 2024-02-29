import re
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders.parsers import LanguageParser
from tempfile import NamedTemporaryFile
import logging
logger = logging.getLogger(__name__)


class InfoLoader():
    def __init__(self, config):
        '''
        Class for handling all data extraction and chunking
        Inputs:
            config - dictionary from yaml file, containing all important parameters
        '''
        self.config = config
        self.remove_leftover_delimiters = config['splitter_options']['remove_leftover_delimiters']

        # Main list of all documents
        self.document_chunks_full = []
        self.document_names = []

        if config['splitter_options']['use_splitter']:
            self.splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON,
                chunk_size=config['splitter_options']['chunk_size'],
                chunk_overlap=config['splitter_options']['chunk_overlap']
            )
        else:
            self.splitter = None
        logger.info('InfoLoader instance created')
    
    def get_chunks(self, uploaded_files):
        self.document_chunks_full = []
        self.document_names = []

        def remove_delimiters(document_chunks : list):
            # Helper function to remove remaining delimiters in document chunks
            for chunk in document_chunks:
                for delimiter in self.config['splitter_options']['delimiters_to_remove']:
                    chunk.page_content = re.sub(delimiter, ' ', chunk.page_content)
            return document_chunks
        
        def get_py(file_path, file_name):
            # Load Py files
            loader = GenericLoader.from_filesystem(
                file_path,
                parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
            )
            if self.splitter:
                document_chunks = self.splitter.split_documents(loader.load())
            else:
                document_chunks = loader.load()

            return document_chunks
        
        def get_txt(file_path, file_name):
            loader = TextLoader(temp_file_path, autodetect_encoding=True)

            if self.splitter:
                document_chunks = self.splitter.split_documents(loader.load())
            else:
                document_chunks = loader.load()
            return document_chunks
        
        for file_index, file in enumerate(uploaded_files):

            # Get the file type and file name
            file_type = file.name.split('.')[-1].lower()
            logger.info(f'\tSplitting file {file_index+1} : {file.name}')
            file_name = ''.join(file.name.split('.')[:-1])

            with NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(file.read())

            # Handle different file types
            if file_type =='py':
                document_chunks = get_py(temp_file_path, file_name)
            elif file_type == 'txt':
                document_chunks = get_txt(temp_file_path, file_name)

            # Additional wrangling - Remove leftover delimiters and any specified chunks
            if self.remove_leftover_delimiters:
                document_chunks = remove_delimiters(document_chunks)
            
            self.document_chunks_full.extend(document_chunks)
            
            

        


