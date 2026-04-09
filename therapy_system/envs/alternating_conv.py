from therapy_system.agents.agents import Agent
from therapy_system.envs.conversation import Conv
from typing import List
from therapy_system.action import Action
from enum import Enum
from collections.abc import Iterator
from typing import Any, Union, Tuple
import re
import types

from therapy_system.action.therapy.prompts import (
    parse_persuasive_therapist_output,
    stream_persuasive_llm_chunks,
)

# create enum for game state
class Turn(Enum):
    ASSISTANT = 0
    USER = 1

class AlternatingConv(Conv):
    """
    An alternating game is a game type whereby players take turns to make moves

    A game requires implementation of

    (1) rules (`game_prompt`): A textual description of the context, rules, and objectives of the ratbench

    # (2) Parser: implement a parser to extract game state from text

    (3) read/write state (`write_game_state` / `read_game_state`): determines information flow between players

    (4) `get_next_player`: determines who goes next

    (5) `is_end_state`: determines if the game has ended

    (6) `check end state`: determines the objective is met or not

    """

    def __init__(self, 
                 agents: List[dict],
                 transit: List[str],
                 init_message: str = None,
                 persuasion_flag: bool = False,
                 words_limit: int = 100,
                 log_dir=".logs",
                 log_path=None,
                 game_state=None,
    ):
        '''
        agents: List of agents with their respective configurations
        [
            {"agent_name": AGENT_NAME,
            "agent_model": AGENT_MODEL,
            "system_message": SYSTEM_MESSAGE,
            "action_space": ACTION_SPACE}, 
        ]
        '''
        super().__init__(log_dir, log_path)
        self.state = 0
        self.transit = transit
        self.persuasion_flag = persuasion_flag
        self.words_limit = words_limit
        self.game_state = game_state if game_state is not None else []
        self.init_message = init_message

        self.players = self.init_players(agents, self.game_state, transit)

    def read_iteration_message(self, iteration):
        message = self.game_state[iteration].get(
            "response", None
        )
        return message if message is not None else ""

    def sample_action(self) -> Action:
        action_space = self.transit[self.state]
        return self.players[action_space].action_space.sample()

    def extract_persuasion_response(self, text):
        """
        Extract technique + therapist reply: JSON (Pydantic-validated) preferred;
        falls back to legacy <technique>/<response> tags, then raw text.
        """
        chat_response_str = "".join(text) if isinstance(text, types.GeneratorType) else text

        print(f"Chat response: {chat_response_str}")

        parsed = parse_persuasive_therapist_output(chat_response_str)
        if parsed is not None:
            technique_text = parsed.technique if parsed.technique != "None" else None
            return technique_text, parsed.response

        technique = re.search(r"<technique>(.*?)</technique>", chat_response_str)
        response = re.search(r"<response>(.*?)</response>", chat_response_str)

        if not technique and not response:
            technique_text = None
            response_text = chat_response_str
        elif not technique:
            response_text = response.group(1)
            technique_text = None
        elif not response:
            technique_text = technique.group(1)
            response_text = chat_response_str
        else:
            technique_text = technique.group(1)
            response_text = response.group(1)

        return technique_text, response_text

    
    # def update_technique_in_game_state(self, technique: str):
    #     """Update the persuasion technique in the most recent game state entry"""
    #     if not self.game_state:
    #         return
    #     self.game_state[-1]['persuasion_technique'] = technique
    

    def get_response(
        self, action: Action
    ) -> Tuple[Any, Union[str, Iterator[str]]]:
        next = self.transit[self.state]
        # Print current state index and next player for debugging
        # print(f"Current state index: {self.state}")
        # print(f"Next player to act: {next}")
        if (self.state == 0) and (self.init_message):
            response = self.init_message
        else:
            last_message = self.read_iteration_message(self.state)
            # adding persona, conversation history
            persona = self.players[next].get_persona()
            conversation = self.players[next].get_conversation()

            prompt = action(last_message, persona, conversation, self.persuasion_flag, self.words_limit)

            response = self.players[next].chat(prompt)
        
        # Extract technique if persuasion_flag is set
        technique = None
        if self.persuasion_flag:
            if isinstance(response, types.GeneratorType):
                technique_box, body_gen = stream_persuasive_llm_chunks(response)
                return technique_box, body_gen
            technique, response = self.extract_persuasion_response(response)
            print(f"In alternating conversation: {technique}, {response}")
            return technique, response

        return technique, response


    def step(self, action: Action, technique: str = None, response: str = None):
        """
        Should return (observagtion: ObsType, reward: float, terminated: bool, truncated: bool, info: dict)
        """
        terminated, truncated = False, False
        reward = None
        next = self.transit[self.state]

        if response is None:
            technique, response = self.get_response(action)
            # For the scripted init_message, chat() is never called so we track manually.
            # All other turns are tracked inside Agent.chat().
            if (self.state == 0) and self.init_message:
                resp_str = response if isinstance(response, str) else "".join(response)
                self.players[next].update_conversation_tracking("assistant", resp_str)
        else:
            # External response bypassed chat(); track it manually.
            self.players[next].update_conversation_tracking("assistant", response)

        terminated = self.is_end_state()
        truncated = self.is_truncated_state()
        info = self.get_info()
        if terminated or truncated:
            reward = self.get_reward()

        self.write_game_state(
            player=self.players[next],
            response=response,
            reward=reward, 
            terminated=terminated,
            truncated=truncated,
            persuasion_technique=technique
        )
            # persuasion_technique=technique)
        
        self.get_next_player()

        return response, reward, terminated, truncated, info
    
    def get_info(self) -> dict:
        return {
            "name": self.players[self.transit[self.state]].name
        }
    
    def is_truncated_state(self):
        return self.state >= len(self.transit)
    
    def write_game_state(self,
                         player: Agent,
                         response: str,
                         reward: int,
                         terminated: bool,
                         truncated: bool, 
                         persuasion_technique: str = None):
            
        curr_state = dict(
            current_iteration=self.state,
            response=response,
            player=player.name,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            action=player.action_space,
            persuasion_technique=persuasion_technique
        )
        self.game_state.append(curr_state)
    
    def update_game_state(self,
                         response: str,
                         reward: int,
                         terminated: bool,
                         truncated: bool):
        if not self.game_state:
            raise IndexError("The game_state list is empty.")
        
        last_entry = self.game_state[-1]
        last_entry['response'] = response
        last_entry['reward'] = reward
        last_entry['terminated'] = terminated
        last_entry['truncated'] = truncated

    def get_next_player(self):
        self.state += 1