# py-assistant

Py-assistant is an interactive chatbot specifically focusing on Python. Our goal is to: 1. Classify user's prompt as code summarization, code translation, or code generation; 2. Proceed with the described task in only one open-source model.

![UI](docs/UI.png)

Our progress is described as the following:

Sprint 1:
* Progress: We built basic UI namely "LLM Chatbot" and "Code Summarization". We made decisions on the LLM we will use.
    * For "LLM Chatbot" interface, the user can choose to use openai as a client or to use claude. Since we have not received credits from openai, our demo will be focusing on displaying py-assistant with anthropic. 
    * For "Code Summarization", the user can choose the mode of interacting with py-assistant. Specifically, the user can choose either chat with py-assistant or submit a .py or .txt file.
    * Decision on LLM model for py-assistant: we will use StarCoder (https://arxiv.org/abs/2305.06161) and SteloCoder (https://arxiv.org/abs/2310.15539). It is a 15.5B model focusing on python code. StarCoder is designed as Python code generation assistant, and SteloCoder is designed as 5 Programming Language to Python translation. In the end, we will seek ways to merge the three fine-tuned model together to optimize memory usage.
* Contributions:
    * Tess works on building the streamlit app 'LLM Chatbot.py' with OpenAI as the backend model, as well as adding the page 'Code_Summarization.py' that allows users to upload code files directly into the app for code summarization.
    * Joyce works on adding functionality of choosing which LLM model to use on the backend (openai or claude) for 'LLM Chatbot.py', as well as adding functionality of choosing user interaction mode (chat mode or file input) for 'Code_Summarization.py'
    * Both of the teammates research on state-of-the-art LLMs and choose which LLM to use for backend in the future.
* Notes on progress:
    * For "LLM Chatbot" interface, our next step is to modify it to first classify user's prompt and then proceed with the identified task.
    * We are going to build other interfaces. Specifically, other than "Code Summarization", we will build "Code Generation", and "Code Translation". In the end, the user can choose to use the unified mode (LLM Chatbot) or task designated mode (one of the three interfaces mentioned above).

Sprint 2:
* Progress & Contributions:
    * Tess: 
    1) Built the "Code_Translation.py" page, designed to enable users to either upload code files or interact with a LLM to translate Python code into Java, C++, JavaScript, or Go. Specifically, this page will execute a two-step process based on user input. First, it will run a pre-check to make sure that the provided Python code is suitable for translating into the target language. If the code is deemed suitable, the translation process is initiated. Otherwise, the process will be halted.
    2) Modified the page "LLM Chatbot.py" so that it will first classify user prompt into code generation, code summarization, or code translation. Then, the chatbot will proceed with the identified coding task.
    3) Future plan: Tess will further enrich the LLM Chatbot page so that it will support more sophisticated functionality based on the identified task. Tess will also modify the file upload section in the Code_Summarization.py page to enable RAG functionality, so that the app will retrieve relevant information from the uploaded file and generate more precise answers.
    
    * Joyce:
    Majorly focused on fine-tuning StarCoder for Code Summarization. 
    1) Preprocessed the XLCoST dataset and outputs training/val/test dataset for python code - summarization pairs. 
        * Datasets description: The raw dataset is from XLCoST dataset which is a comprehensive dataset focusing on all tasks of coding. The original dataset is stored in 'finetune code summarization/datasets_summarization/pair_data_tok_1_comment/Python-comment' for code snippets summarization and 'finetune code summarization/datasets_summarization/pair_data_tok_full_desc/Python-comment' for python programs. 
        * Processed dataset: The output file is stored in 'finetune code summarization/datasets_summarization/process_data'. For snippet level python code summarization, we have 81.2K training pairs, 3.9K validation data pairs, and 7.3K test data pairs. For program level samples, we have 9.3K training pairs, 472 validation pairs, and 887 test pairs. All files are stored in .json format and can be passed in fine-tuning datasets. One observation for the dataset is that there is some noise, meaning that there are some samples that inaccurately summarize the actual python code. However, the chances of noise are low, so we ignore this issue.
        * Notebook: The notebook for data preprocessing is named as 'data_preprocessing.ipynb'. 
    2) Completed the script for fine-tuning StarCoder on code summarization. 
        * The major components include: 
            a) an IterableDataset named SummarizationDataset. Basically, it takes json file (as what we preprocessed), encodes the samples, transfers into the data used in final training step.
            b) Low-Rank Adaptation method (LoRA):  We cite from the paper LoRA: Low-Rank Adaptation of Large Language Models (https://arxiv.org/abs/2106.09685). It claims that when we fine-tune, we only need to modify the first few ranks of the matrices. In practice, it yields good result with high efficiency in terms of time and storage. In the end, we only need to save LoRA metrices which is only 0.05% of total number of parameters. We can use lora in peft implemented by huggingface.
            c) Normal training config
    3) Future work: Due to the complications for credits, we are not able to perform fine-tuning. After receiving the credits, we are going to fine-tune StarCoder on code summarization, get the LoRA matrices, and merge them into StarCoder along with code translation and generation tasks.

Sprint 3:
* Progress & Contributions:
    * Tess: 
        1) Successfully implemented the Retrieval-Augmented Generation (RAG) functionality on the "Code_Summarization" page utilizing LangChain. This enhancement allows users to upload multiple files for embedding, enabling the RAG system to efficiently retrieve the most relevant documents based on a user's query. Consequently, this system provides precise answers by leveraging the context provided by the user's input with the LLM of choice. Moreover, the RAG system has memory for past chat history, allowing users to maintain a continuous conversation with the chatbot.
        2) Demo day plan: Tess will include further developments to the LLM Chatbot page. Should our efforts to fine-tune our model for the final demo prove successful, Tess will integrate this optimized model for the specified tasks. Additionally, Tess is set to expand the chatbot's functionality by incorporating advanced prompting techniques, such as the Chain-of-Thought approach, to enhance its utility and user experience. On the demo day, Tess will showcase the capabilities of Py-assistant end-to-end, using different LLM backends for specific coding tasks.

* Testing Instruction:
    * Code Translation: To evaluate the capabilities of our code translator, users are encouraged to initially present the chatbot with a Python script that incorporates distinct Python libraries (like OpenAI), enabling the chatbot to determine its incompatibility for translation to the chosen target language. 
    Subsequently, users should submit a Python file featuring an object-oriented programming structure to the chatbot, which will allow for an accurate translation of the content into the corresponding language of choice.
    * Code Summarization: We invite users to explore the capabilities of the Retrieval-Augmented Generation (RAG) feature by uploading 3-4 Python files and posing a specific question concerning the code. Following this, users will experience the RAG system in action, as it responds to the query using retrieved source documents to provide context and deliver accurate answers. 