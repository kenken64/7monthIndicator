"""
Unified LLM Provider Abstraction
Supports both OpenAI and DeepSeek APIs with a consistent interface
"""

import os
import base64
import requests
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from openai import OpenAI


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion"""
        pass

    @abstractmethod
    def chat_completion_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_data: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion with vision capabilities"""
        pass

    @abstractmethod
    def get_model_name(self, model_type: str = "default") -> str:
        """Get the appropriate model name for this provider"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=self.api_key)
        self.base_url = "https://api.openai.com/v1"

        # Model mappings
        self.models = {
            "default": "gpt-5-nano",
            "fast": "gpt-5-nano",
            "smart": "gpt-4o",
            "vision": "gpt-4o",
            "mini": "gpt-4o-mini"
        }

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenAI"""
        model = model or self.models["default"]

        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens

        if response_format:
            params["response_format"] = response_format

        params.update(kwargs)

        response = self.client.chat.completions.create(**params)

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def chat_completion_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_data: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion with vision using OpenAI"""
        model = model or self.models["vision"]

        # Prepare messages with image
        vision_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), str):
                vision_messages.append(msg)
            else:
                vision_messages.append(msg)

        # Add image if provided
        if image_data:
            if vision_messages and vision_messages[-1]["role"] == "user":
                # Convert text content to array format
                text_content = vision_messages[-1]["content"]
                vision_messages[-1]["content"] = [
                    {"type": "text", "text": text_content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}",
                            "detail": kwargs.get("detail", "high")
                        }
                    }
                ]

        payload = {
            "model": model,
            "messages": vision_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1500
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return {
            "content": result["choices"][0]["message"]["content"],
            "model": result["model"],
            "usage": result.get("usage", {})
        }

    def get_model_name(self, model_type: str = "default") -> str:
        """Get the OpenAI model name"""
        return self.models.get(model_type, self.models["default"])


class DeepSeekProvider(LLMProvider):
    """DeepSeek API Provider"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable.")
        self.base_url = "https://api.deepseek.com"

        # Model mappings
        self.models = {
            "default": "deepseek-chat",
            "fast": "deepseek-chat",
            "smart": "deepseek-chat",
            "vision": "deepseek-chat",  # DeepSeek may not support vision yet
            "coder": "deepseek-coder",
            "mini": "deepseek-chat"
        }

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion using DeepSeek"""
        model = model or self.models["default"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Note: DeepSeek may not support response_format, handle gracefully
        if response_format and response_format.get("type") == "json_object":
            # Add instruction to messages instead
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += "\n\nIMPORTANT: You must respond with ONLY valid JSON. Do not include any other text before or after the JSON."

        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return {
            "content": result["choices"][0]["message"]["content"],
            "model": result["model"],
            "usage": result.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }

    def chat_completion_with_vision(
        self,
        messages: List[Dict[str, Any]],
        image_data: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion with vision using DeepSeek"""
        # Note: DeepSeek may not support vision API yet
        # This implementation falls back to text-only or raises an informative error

        if image_data:
            print("Warning: DeepSeek may not support vision API. Attempting text-only completion.")
            # Remove image-related content and use text only
            text_messages = []
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    text_messages.append(msg)
                elif isinstance(msg.get("content"), list):
                    # Extract text from array content
                    text_parts = [item["text"] for item in msg["content"] if item.get("type") == "text"]
                    if text_parts:
                        text_messages.append({
                            "role": msg["role"],
                            "content": " ".join(text_parts)
                        })

            return self.chat_completion(
                messages=text_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def get_model_name(self, model_type: str = "default") -> str:
        """Get the DeepSeek model name"""
        return self.models.get(model_type, self.models["default"])


class LLMProviderFactory:
    """Factory for creating LLM providers"""

    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> LLMProvider:
        """
        Create an LLM provider based on configuration

        Args:
            provider_name: "openai" or "deepseek". If None, reads from LLM_PROVIDER env var

        Returns:
            LLMProvider instance
        """
        provider_name = provider_name or os.environ.get("LLM_PROVIDER", "openai").lower()

        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "deepseek":
            return DeepSeekProvider()
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}. Supported: 'openai', 'deepseek'")

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers"""
        return ["openai", "deepseek"]


# Convenience function
def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Get an LLM provider instance"""
    return LLMProviderFactory.create_provider(provider_name)


if __name__ == "__main__":
    # Example usage
    print("Available LLM Providers:", LLMProviderFactory.get_available_providers())

    # Example with OpenAI
    try:
        provider = get_llm_provider("openai")
        print(f"Created OpenAI provider with model: {provider.get_model_name('default')}")
    except Exception as e:
        print(f"OpenAI provider error: {e}")

    # Example with DeepSeek
    try:
        provider = get_llm_provider("deepseek")
        print(f"Created DeepSeek provider with model: {provider.get_model_name('default')}")
    except Exception as e:
        print(f"DeepSeek provider error: {e}")
