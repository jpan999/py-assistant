# this file is to create an index that will store the embeddings of all the code present in the files listed in the github repo

# LangChain
from langchain.llms import VertexAI
from langchain.embeddings import VertexAIEmbeddings

from langchain.schema import HumanMessage, SystemMessage
from langchain.schema.document import Document

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.text_splitter import Language

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

import time
from typing import List
from pydantic import BaseModel

# Vertex AI
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import CodeGenerationModel

import requests, time

GITHUB_TOKEN = "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"
GITHUB_REPO = "GoogleCloudPlatform/generative-ai" # @param {type:"string"}

#Crawls a GitHub repository and returns a list of all ipynb files in the repository
def crawl_github_repo(url,is_sub_dir,access_token = f"{GITHUB_TOKEN}"):

    ignore_list = ['__init__.py']

    if not is_sub_dir:
        api_url = f"https://api.github.com/repos/{url}/contents"
    else:
        api_url = url

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {access_token}" 
                   }

    response = requests.get(api_url, headers=headers)
    response.raise_for_status()  # Check for any request errors

    files = []

    contents = response.json()

    for item in contents:
        if item['type'] == 'file' and item['name'] not in ignore_list and (item['name'].endswith('.py') or item['name'].endswith('.ipynb')):
            files.append(item['html_url'])
        elif item['type'] == 'dir' and not item['name'].startswith("."):
            sub_files = crawl_github_repo(item['url'],True)
            time.sleep(.1)
            files.extend(sub_files)

    return files

code_files_urls = crawl_github_repo(GITHUB_REPO,False,GITHUB_TOKEN)

# Write list to a file so you do not have to download each time
with open('code_files_urls.txt', 'w') as f:
    for item in code_files_urls:
        f.write(item + '\n')