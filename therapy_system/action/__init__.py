from therapy_system.action.action import Action, ActionSpace
from therapy_system.action.therapy import TherapyActionSpace
from therapy_system.action.human_action import HumanActionSpace
from typing import Dict

def get_action_space(action_space: Dict[str, any]) -> ActionSpace:
    action_space_name = action_space["name"]
    if action_space_name == "therapy":
        return TherapyActionSpace(action_space["action"])
    elif action_space_name == "human":
        return HumanActionSpace()
    else:
        raise ValueError(f"Unknown action space: {action_space_name}")