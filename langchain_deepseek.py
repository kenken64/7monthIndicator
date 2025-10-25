"""
LangChain-compatible DeepSeek wrapper for CrewAI integration
"""

import os
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
import requests


class ChatDeepSeek(BaseChatModel):
    """
    LangChain-compatible wrapper for DeepSeek API

    This allows DeepSeek to be used with CrewAI and other LangChain-based tools
    """

    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    deepseek_api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.deepseek_api_key:
            self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY must be set")

    @property
    def _llm_type(self) -> str:
        """Return type of language model."""
        return "deepseek"

    def _convert_messages_to_deepseek_format(
        self, messages: List[BaseMessage]
    ) -> List[dict]:
        """Convert LangChain messages to DeepSeek API format"""
        deepseek_messages = []

        for message in messages:
            if isinstance(message, HumanMessage):
                deepseek_messages.append({
                    "role": "user",
                    "content": message.content
                })
            elif isinstance(message, SystemMessage):
                deepseek_messages.append({
                    "role": "system",
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                deepseek_messages.append({
                    "role": "assistant",
                    "content": message.content
                })
            else:
                # Default to user message
                deepseek_messages.append({
                    "role": "user",
                    "content": str(message.content)
                })

        return deepseek_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response from DeepSeek API"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }

        deepseek_messages = self._convert_messages_to_deepseek_format(messages)

        payload = {
            "model": self.model,
            "messages": deepseek_messages,
            "temperature": self.temperature,
        }

        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens

        if stop:
            payload["stop"] = stop

        # Merge additional kwargs
        payload.update(kwargs)

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # Extract the response content
            if result.get("choices") and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                generation = ChatGeneration(
                    message=AIMessage(content=content),
                    generation_info=result.get("usage", {})
                )

                return ChatResult(generations=[generation])
            else:
                raise ValueError("No response from DeepSeek API")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"DeepSeek API request failed: {e}")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate - for now, just call sync version"""
        # For simplicity, using sync version
        # In production, you'd want to use aiohttp for true async
        return self._generate(messages, stop, **kwargs)


def get_langchain_llm(provider: Optional[str] = None, **kwargs):
    """
    Get a LangChain-compatible LLM instance

    Args:
        provider: "openai" or "deepseek". If None, reads from LLM_PROVIDER env var
        **kwargs: Additional arguments for the LLM

    Returns:
        BaseChatModel instance
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        return ChatOpenAI(
            openai_api_key=api_key,
            **kwargs
        )

    elif provider == "deepseek":
        # Use ChatOpenAI with DeepSeek's endpoint for better CrewAI compatibility
        from langchain_openai import ChatOpenAI

        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

        return ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=kwargs.get('model', 'deepseek-chat'),
            temperature=kwargs.get('temperature', 0.7)
        )

    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: 'openai', 'deepseek'")


if __name__ == "__main__":
    # Test the DeepSeek wrapper
    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Test DeepSeek
        print("Testing DeepSeek LangChain wrapper...")
        llm = get_langchain_llm("deepseek", model="deepseek-chat", temperature=0.7)

        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2?")
        ]

        result = llm.invoke(messages)
        print(f"Response: {result.content}")
        print("✅ DeepSeek test successful!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
