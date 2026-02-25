import os
import requests
import json
from typing import Optional, Dict, Any

class LLMFactory:
    @staticmethod
    def create_client(provider: str, api_key: str, model: Optional[str] = None):
        if provider == "openai":
            return OpenAIClient(api_key, model=model)
        elif provider == "anthropic":
            return AnthropicClient(api_key, model=model)
        elif provider == "deepseek":
            return DeepseekClient(api_key, model=model)
        elif provider == "gemini_pro":
            return GeminiProClient(api_key)
        else:
            return None

class BaseLLMClient:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = (model or "").strip() or None

    def generate_content(self, prompt: str) -> str:
        raise NotImplementedError

class OpenAIClient(BaseLLMClient):
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)

    def generate_content(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model = self.model or self.DEFAULT_MODEL
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return f"Error calling OpenAI: {str(e)}"

class DeepseekClient(BaseLLMClient):
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)

    def generate_content(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model = self.model or self.DEFAULT_MODEL
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Deepseek Error: {e}")
            return f"Error calling Deepseek: {str(e)}"

class AnthropicClient(BaseLLMClient):
    DEFAULT_MODEL = "claude-3-5-sonnet-20240620"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)

    def generate_content(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        model = self.model or self.DEFAULT_MODEL
        data = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
            response.raise_for_status()
            return response.json()['content'][0]['text']
        except Exception as e:
            print(f"Anthropic Error: {e}")
            return f"Error calling Anthropic: {str(e)}"

class GeminiProClient(BaseLLMClient):
    def generate_content(self, prompt: str) -> str:
        # Using the REST API for consistency, though we have the SDK
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini Pro Error: {e}")
            return f"Error calling Gemini Pro: {str(e)}"
