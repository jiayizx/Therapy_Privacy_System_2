from abc import ABC, abstractmethod
import copy
from typing import Generator, Union
from therapy_system.utils import escape_special_characters, unescape_special_characters

class LM_Agent(ABC):
    def __init__(self,
                 engine="gpt-3.5-turbo",
                 temperature=0.7,
                 max_tokens=8192,
                 stream=False,
                 ):
        self.engine = engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream    
    

    def chat(self, messages) -> Union[str, Generator[str, None, None]]:
        if self.stream:
            return escape_special_characters(self._chat_with_stream(messages))
        else:
            return escape_special_characters(self._chat(messages))

    @abstractmethod
    def _chat(self, messages) -> str:
        pass

    @abstractmethod
    def _chat_with_stream(self, messages) -> Generator[str, None, None]:
        pass
