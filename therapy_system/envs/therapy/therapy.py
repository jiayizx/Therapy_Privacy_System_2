from therapy_system.agents import Agent
from therapy_system.envs import AlternatingConv, Turn
from therapy_system.action import get_action_space
from typing import List, Dict
import re
from therapy_system.action.therapy import TAXONOMY


class Therapy(AlternatingConv):
    def __init__(
        self,
        agents: List[dict],
        transit: List[str],
        init_message: str = None,
        persuasion_flag: bool = False,
        words_limit: int = 100,
        log_dir=".logs",
        log_path=None,
        game_state=None,
    ):
        super().__init__(agents, transit, init_message, persuasion_flag, words_limit, log_dir, log_path, game_state)
        self.game_state : List[dict] = [
            {
                "current_iteration": "START",
                "turn": None,
                "settings": {
                    "player": [player for player in self.players],
                    "model": [agent.engine for _, agent in self.players.items()],
                    "action": [agent.action_space for _, agent in self.players.items()],
                    "prolific_id": [agent.prolific_id for _, agent in self.players.items()],
                    # "api": [agent.api for _, agent in self.players.items()]
                }
            }
        ]

    def init_players(self, agents, game_state, transit) -> Dict[str, Agent]:
        roles = [p['role'] for p in agents]
        assert all([t in roles for t in set(transit)]), f"Transit roles {transit} must be subset of agent roles {roles}"

        players = {
            p['name'] : Agent(
                name=p['name'],
                engine=p['engine'],
                system=p['system'],
                persona=p['persona'] if 'persona' in p else {},
                model_args=p['model_args'] if 'model_args' in p else {},
                action_space=get_action_space(p['action_space']),
                prolific_id=p['prolific_id'] if 'prolific_id' in p else None,
                # api=p['api'] if 'api' in p else None,
            )
            for p in agents
        }
        return players
    
    def get_reward(self):
        return self.donor_price if self.is_end_state() else 0
    
    def contains_donate_amount(self, text):
        pattern = r"donate \$\d+"
        match = re.search(pattern, text)
        
        return bool(match)
    
    def is_end_state(self):
        if len(self.game_state) <= 3:
            return False
        second_last = self.game_state[-2]
        if (second_last['player'] == "assistant"):
            return False
        # check if "donate $X" is in the second last message using regex
        message = second_last['response']
        if self.contains_donate_amount(message):
            self.donor_price = re.search(r"donate \$(\d+)", message).group(1)
            return True
        return False
    
    def after_end_state(self):
        return f"The user is willing to donate ${self.donor_price}! Thank you for your donation!"
