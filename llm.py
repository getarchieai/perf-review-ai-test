# Related third-party imports
import abc
import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, List, Optional

# LangChain and model-specific imports
from groq import Groq
import openai
import anthropic
import google.generativeai as genai

# Environment setup
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)

MODEL_MAPPING = {
    "openai": {
        "small": "gpt-3.5-turbo-0125",
        "medium": "gpt-4",
        "large": "gpt-4-turbo"
    },
    "anthropic": {
        "small": "claude-3-haiku-20240307",
        "medium": "claude-3-sonnet-20240229",
        "large": "claude-3-opus-20240229"
    },
    "groq": {
        "small": "llama3-8b-8192",
        "medium": "llama3-13b-8192",
        "large": "mixtral-8x7b-32768"
    },
    "google": {
        "small": "gemini-1.5-flash-latest",
        "medium": "gemini-1.0-pro",
        "large": "gemini-1.5-pro-latest"
    }
}

class LLM(abc.ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abc.abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        pass

    @abc.abstractmethod
    def stream_text(self, prompt: str, **kwargs):
        pass

class OpenAILLM(LLM):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or OPENAI_API_KEY)
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_text(self, prompt: str, model: str = "large", **kwargs) -> str:
        model_name = MODEL_MAPPING["openai"][model]
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.2),
        )
        return response.choices[0].message.content
    
    def stream_text(self, prompt: str, model: str = "large", **kwargs):
        model_name = MODEL_MAPPING["openai"][model]
        messages = [{"role": "user", "content": prompt}]
        stream = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.2),
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].message['content'] is not None:
                yield chunk.choices[0].message['content']

class AnthropicLLM(LLM):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or ANTHROPIC_API_KEY)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_text(self, prompt: str, model: str = "large", **kwargs) -> str:
        model_name = MODEL_MAPPING["anthropic"][model]
        response = self.client.messages.create(
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2048),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    def stream_text(self, prompt: str, model: str = "large", **kwargs):
        model_name = MODEL_MAPPING["anthropic"][model]
        messages = [{"role": "user", "content": prompt}]
        with self.client.messages.stream(
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2048),
            messages=messages,
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk
    

class GroqLLM(LLM):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or GROQ_API_KEY)
        self.client = Groq(api_key=self.api_key)

    def generate_text(self, prompt: str, model: str = "medium", **kwargs) -> str:
        model_name = MODEL_MAPPING["groq"][model]
        messages = [{"role": "system", "content": prompt}]
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.2),
        )
        return response.choices[0].message.content
    
class GoogleLLM(LLM):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or GOOGLE_API_KEY)
        genai.configure(api_key=self.api_key)

    def generate_text(self, prompt: str, model: str = "large", **kwargs) -> str:
        model_name = MODEL_MAPPING["google"][model]
        generation_config = {
            "temperature": kwargs.get("temperature", 0.2),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 64),
            "max_output_tokens": kwargs.get("max_tokens", 8192),
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
        response = model.generate_content(prompt)
        return response.text

    def stream_text(self, prompt: str, model: str = "large", **kwargs):
        model_name = MODEL_MAPPING["google"][model]
        generation_config = {
            "temperature": kwargs.get("temperature", 0.2),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 64),
            "max_output_tokens": kwargs.get("max_tokens", 8192),
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
        for chunk in model.generate_content(prompt, stream=True):
            yield chunk.text