from openai import OpenAI
import anthropic
import streamlit as st
import re
import warnings
warnings.filterwarnings("ignore")

INITIAL_MESSAGE = [
    {"role": "user", "content": "Hi!"},
    {
        "role": "assistant",
        "content": "Hey there, I'm your Python-speaking coding assistant, ready to answer your questions regarding Python code!💻 Please let me know if you are new to Python!",
    },
]

class LLMChatbot:
    '''
    Implement a common interface that can handle the specifics of each API
    '''
    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = INITIAL_MESSAGE.copy()
        self.model = None
        self.model_type = None
    
    def set_model(self, model_type):
        self.model_type = model_type
        if model_type.startswith("gpt-"):
            self.model = OpenAI(api_key=self.api_key)
        elif model_type == "claude-1.3":
            self.model = anthropic.Client(api_key=self.api_key)

    def retrieve_beginner_status(self, prompt):
        classification_prompt = f"Based on the user input, classify if user is a beginner to Python or not. Specifically, check if the user wants to understand basic python coding, or python history, etc. If the user is a beginner to Python, type 'yes'; otherwise, type 'no'."

        if self.model_type == "gpt-3.5-turbo":

            response = self.model.chat.completions.create(model=self.model_type, messages=[
                {"role": "system", "content": "I am an assistant capable of classifying user's status."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": classification_prompt},
            ])
            status = response.choices[0].message.content
            
        else:

            response = self.model.completions.create(
                prompt=f"""{anthropic.HUMAN_PROMPT} Here's the user input: {prompt} {classification_prompt} {anthropic.AI_PROMPT}""",
                stop_sequences=[anthropic.HUMAN_PROMPT],
                model=self.model_type,  
                max_tokens_to_sample=300,
            )
            status = response.completion
        status = status.lower()
        
        if "yes" in status:
            status = 1
        else:
            status = 0
        return status
       
    def get_user_intent(self, prompt):
        classification_prompt = f"Based on the user input, classify the user's intent. If the user does not mention he/she is a beginner to python, then search for keywords such as 'summarize', 'generate', 'translate' to detect user's intent. Is the user asking for code generation, code summarization, or code translation? "

        if self.model_type.startswith("gpt-"):

            response = self.model.chat.completions.create(model=self.model_type, messages=[
                {"role": "system", "content": "I am a coding assistant capable of classifying user intent."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": classification_prompt},
            ])
            intent = response.choices[0].message.content
        else:

            response = self.model.completions.create(
                prompt=f"""{anthropic.HUMAN_PROMPT} Here's the user input: {prompt} {classification_prompt} {anthropic.AI_PROMPT}""",
                stop_sequences=[anthropic.HUMAN_PROMPT],
                model=self.model_type,  
                max_tokens_to_sample=300,
            )
            intent = response.completion
        intent = intent.lower()
        
        if "code generation" in intent:
            intent = "code generation"
        elif "code summarization" in intent:
            intent = "code summarization"
        elif "code translation" in intent: 
            intent = "code translation"
        else:
            intent = None
        return intent
    
    def check_trans_suitability(self, prompt, target_language):
        suitability_prompt = f"Check if the following code is suitable for translation to {target_language}: {prompt}. Criteria for suitability include simplicity, clarity, and absence of highly Python-specific features. If suitable, please return 'suitable' as the answer. Else, please return an error message that contains 'not suitable' and explains your reasoning."
        response = self.model.chat.completions.create(model=self.model_type, messages=[
            {"role": "system", "content": "I am a coding assistant capable of translating Python code into other coding languages."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": suitability_prompt},
        ])
        suitability_response = response.choices[0].message.content
        suitable = 1
        if "not suitable" in suitability_response.lower():
            suitable = 0
        return suitable, suitability_response
    
    def check_gen_suitability(self, prompt):
        suitability_prompt = f"Check if the following code is suitable for code generation. Specifically, please check if users use any keywords that elaborate to generate programming language code such as 'function', 'write', or 'define', or 'make'. If suitable, please return 'suitable' as the answer. Else, please return an error message that says 'not suitable' and states why it's not suitable."
        response = self.model.chat.completions.create(model=self.model_type, messages=[
            {"role": "system", "content": "I am a coding assistant capable of translating your human language into Python functions."},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": suitability_prompt},
        ])
        suitability_response = response.choices[0].message.content
        suitable = 1
        if "not suitable" in suitability_response.lower():
            suitable = 0
        return suitable, suitability_response

    def get_reply(self, messages):
        if self.model_type.startswith("gpt-"):
            response = self.model.chat.completions.create(model=self.model_type, messages=messages)
            reply = response.choices[0].message.content
            print(reply)
        else:
            chat_prompt = f"""{anthropic.HUMAN_PROMPT} Here's the user input: {messages} {anthropic.AI_PROMPT}"""
            
            response = self.model.completions.create(
                prompt=chat_prompt,
                stop_sequences=[anthropic.HUMAN_PROMPT],
                model=self.model_type,  
                max_tokens_to_sample=300,
            )
            reply = response.completion
        return reply

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
    
    def generate_beginner_reply(self, prompt):
        self.add_message("user", prompt)
        self.add_message("assistant", f"Based on the input, the user intent is new to Python, need to explain carefully.")
        response = self.get_reply(self.messages)
        self.add_message("assistant", response)
        return response
    
    def generate_reply(self, prompt):
        self.add_message("user", prompt)
        user_intent = self.get_user_intent(prompt)
        if user_intent:
            self.add_message("assistant", f"Based on the input, the user intent is: {user_intent}")
        response = self.get_reply(self.messages)
        self.add_message("assistant", response)
        return response
    
    def generate_translation(self, prompt, target_language):
        self.add_message("user", prompt)
        self.add_message("assistant", f"Please translate the user-input python code into {target_language}. The translated code should be functional and as concise as possible.")
        response = self.get_reply(self.messages)
        self.add_message("assistant", response)
        return response
    
    def generate_pycode(self, prompt):
        self.add_message("user", prompt)
        self.add_message("assistant", f"Please translate the user-input human language into Python code. The translated code should be functional and as concise as possible.")
        response = self.get_reply(self.messages)
        print(response)
        self.add_message("assistant", response)
        return response