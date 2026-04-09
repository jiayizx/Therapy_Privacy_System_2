from abc import ABC, abstractmethod
import copy
from therapy_system.agents.llms import load_llm_agent
from therapy_system.action import ActionSpace
from typing import Union, Generator

class Agent:
    """
    Abstract class for agents
    """

    agent_class = __qualname__

    def __init__(self,
                 name="",
                 engine="gpt-3.5-turbo",
                 system="",
                 model_args={},
                 persona = {},
                 action_space: ActionSpace = None,
                 prolific_id: str = None,
                #  api: str = None,
    ):
        self.chat_model = load_llm_agent(engine, model_args)
        # self.strategy = STRATEGY_MAPPING[strategy if strategy else "default"](**kwargs)
        self.conversation = []
        self.engine = engine
        self.system = system
        self.name = name
        self.persona = persona
        self.action_space = action_space
        self.prolific_id = prolific_id
        # self.api = api 
        
        if system:
            self.update_conversation_tracking("system", system)

    def __str__(self) -> str:
        return self.name
    
    def update_conversation_tracking(self, entity, message):
        self.conversation.append({"role": entity, "content": message})

    def chat(self, message) -> Union[str, Generator[str, None, None]]:
        self.update_conversation_tracking("user", message)
        response = self.chat_model.chat(self.conversation)
        if isinstance(response, str):
            self.update_conversation_tracking("assistant", response)
        return response
    
    def get_persona(self):
        return self.persona

    def get_conversation(self):
        return self.conversation
        