import os
import time
import json
import copy
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
from therapy_system.agents import Agent
from therapy_system.action import Action, ActionSpace
from therapy_system.action.therapy import TAXONOMY
from gymnasium import Env
from gymnasium.core import ObsType, ActType
from typing import Union, Generator
from typing import Tuple

class Conv(Env, ABC):
    """
    Base class for conversation env.

    A raw conversation should take in : 
    (1) players: list of agents (2 or more agents, including human agents)
    (2) Event: event object
    (3) init_message: initial message to start the conversation
    """

    def __init__(self, log_dir=".logs", log_path=None):
        # logging
        timestamp = str(round(time.time() * 1000))
        self.log_dir = os.path.abspath(log_dir)
        self.log_path = (
            os.path.join(self.log_dir, timestamp)
            if log_path is None
            else log_path
        )

    @abstractmethod
    def init_players(self, agents, game_state, transit):
        """
        Initialize the players
        """
        pass

    @abstractmethod
    def is_end_state(self):
        """
        ratbench over logic based on ratbench state
        """
        pass

    @abstractmethod
    def after_end_state(self):
        """
        Parse the end state to determine the result
        """
        pass

    @abstractmethod
    def get_next_player(self):
        """
        Determine who goes next
        """
        pass

    @abstractmethod
    def get_reward(self):
        """
        Determine the reward
        """
        pass

    @abstractmethod
    def get_info(self) -> dict:
        """
        Get additional information
        """
        pass

    @abstractmethod
    def sample_action(self) -> Action:
        """
        Sample an action
        """
        pass
    
    @abstractmethod
    def get_response(self, action: Action) -> Union[str, Generator[str, None, None]]:
        """
        Get the response from the agent
        """
        pass

    def to_dict(self):
        """
        Utility function to convert game state into a dictionary
        """
        return {
            "class": self.__class__.__name__,
            **copy.deepcopy(self.__dict__),
        }

    def log_state(self):
        """
        logging full state
        """
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        chat_history = self.log_human_readable_state() # log human readable state (for debugging)
        return chat_history

        # log full state for resuming the game
        # with open(os.path.join(self.log_path, "game_state.json"), "w") as f:
        #     json.dump(self.to_dict(), f, cls=GameEncoder, indent=2)

    def log_human_readable_state(self): 
        """
        easy to inspect log file
        """
        settings = self.game_state[0]["settings"]
        # print(self.game_state[0])

        # # log meta information
        log_str = ""
        log_str = "Game Settings\n\n"
        for idx, player_settings in enumerate(
            zip(
                *[
                    [(k, str(p)) for p in v]
                    for k, v in settings.items()
                    if isinstance(v, list)
                ]
            )
        ):
            log_str += "Player {} Settings:\n".format(idx + 1)
            log_str += "\n".join(
                ["\t{}: {}".format(_[0], _[1]) for _ in player_settings]
            )
            log_str += "\n\n"
        log_str += "------------------ \n"

        for state in self.game_state[1:]:
            if state["current_iteration"] == "END":
                continue
            data = [
                "Current Iteration: {}".format(state["current_iteration"]),
                # "Turn: {}".format(state["turn"]),
                "Player: {}".format(state["player"]),
                "Response: {}".format(state["response"]),
                "Persuasion Technique: {}".format(state["persuasion_technique"]),
                # "Reward: {}".format(state["reward"]),
                # "Terminated: {}".format(state["terminated"]),
            ]
            log_str += "\n".join(data)
            log_str += "\n\n"

        # write to log-file
        with open(os.path.join(self.log_path, "interaction.log"), "w") as f:
            f.write(log_str)
        
        # print(log_str)
        return log_str