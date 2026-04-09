from openai import OpenAI

from therapy_system.agents.llms.lm_model import LM_Agent
from therapy_system.api_key_utils import get_openai_api_key
from typing import Generator

GPT_MODELS_MAPPING = {
    "openai/gpt-4.1-mini": "gpt-4.1-mini",
    "openai/gpt-4.1": "gpt-4.1",
    "openai/o3-mini": "o3-mini",
}


class OpenAIAgent(LM_Agent):
    def __init__(
        self,
        engine,
        temperature=0.7,
        max_tokens=8192,
        stream=False,
    ):
        if engine in GPT_MODELS_MAPPING:
            engine = GPT_MODELS_MAPPING[engine]
        super().__init__(engine, temperature, max_tokens, stream)
        self._client = None
        self._chat_kwargs = {"temperature": temperature, "max_tokens": max_tokens}
        if "o3" in engine or "o4" in engine:
            self._chat_kwargs = {"max_completion_tokens": max_tokens}

    @property
    def client(self):
        if self._client is None:
            api_key, _ = get_openai_api_key()
            self._client = OpenAI(api_key=api_key) if api_key else OpenAI()
        return self._client

    def _chat(self, messages) -> str:
        return self.client.chat.completions.create(
            model=self.engine,
            messages=messages,
            **self._chat_kwargs,
        ).choices[0].message.content

    def _chat_with_stream(self, messages) -> Generator[str, None, None]:
        chat = self.client.chat.completions.create(
            model=self.engine,
            messages=messages,
            stream=True,
            **self._chat_kwargs,
        )
        for chunk in chat:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content