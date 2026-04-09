import os
from openai import OpenAI

from therapy_system.agents.llms.lm_model import LM_Agent
from typing import Generator

OPENROUTER_MODELS_MAPPING = {
    "Llama-3.1-70B": "meta-llama/llama-3.1-70b-instruct",
    "Llama-3.1-8B": "meta-llama/llama-3.1-8b-instruct",

    "Claude-3.5-Sonnet": "anthropic/claude-3.5-sonnet",
    "Claude-3.5-Haiku": "anthropic/claude-3.5-haiku",

    "Gemini-2.5-Flash": "google/gemini-2.5-flash",

    "DeepSeek-R1": "deepseek/deepseek-r1",
}

class OpenRouterAgent(LM_Agent):
    def __init__(
        self,
        engine,
        temperature=0.7,
        max_tokens=8192,
        stream=False,
    ):
        if engine in OPENROUTER_MODELS_MAPPING:
            engine = OPENROUTER_MODELS_MAPPING[engine]
        super().__init__(engine, temperature, max_tokens, stream)
        self.client = OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    def _chat(self, messages) -> str:
        chat = self.client.chat.completions.create(
            model=self.engine,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return chat.choices[0].message.content

    def _chat_with_stream(self, messages) -> Generator[str, None, None]:
        chat = self.client.chat.completions.create(
            model=self.engine,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in chat:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
