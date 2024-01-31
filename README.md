# py-assistant

Py-assistant is an interactive chatbot specifically focusing on Python. Our goal is to: 1. Classify user's prompt as code summarization, code translation, or code generation; 2. Proceed with the described task in only one open-source model.

Our progress is described as the following:

Sprint 1:
* Progress: We built basic UI namely "LLM Chatbot" and "Code Summarization". We made decisions on the LLM we will use.
    * For "LLM Chatbot" interface, the user can choose to use openai as a client or to use claude. Since we have not received credits from openai, our demo will be focusing on displaying py-assistant with anthropic. 
    * For "Code Summarization", the user can choose the mode of interacting with py-assistant. Specifically, the user can choose either chat with py-assistant or submit a .py or .txt file.
    * Decision on LLM model for py-assistant: we will use StarCoder (https://arxiv.org/abs/2305.06161) and SteloCoder (https://arxiv.org/abs/2310.15539). It is a 15.5B model focusing on python code. StarCoder is designed as Python code generation assistant, and SteloCoder is designed as 5 Programming Language to Python translation. In the end, we will seek ways to merge the three fine-tuned model together to optimize memory usage.
* Contributions:
    * Tess works on building 'LLM Chatbot.py' with openai as the backend model and 'Code_Summarization.py' with file input using streamlit.
    * Joyce works on adding functionality of choosing which LLM model to use on the backend (openai or claude) for 'LLM Chatbot.py', as well as adding functionality of choosing user interaction mode (chat mode or file input) for 'Code_Summarization.py'
    * Both of the teammates research on state-of-the-art LLMs and choose which LLM to use for backend in the future.
* Notes on progress:
    * For "LLM Chatbot" interface, it will be designed as first to classify user's prompt and then proceed with the described task.
    * We are going to build other interfaces. Specifically, other than "Code Summarization", we will build "Code Generation", and "Code Translation". In the end, the user can choose to use the unified mode (LLM Chatbot) or task designated mode (one of the three interfaces mentioned above).