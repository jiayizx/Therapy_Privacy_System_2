import json
import os
import random

from therapy_system.action import Action, ActionSpace
from therapy_system.action.therapy.prompts import build_user_prompt

TAXONOMY = []
with open(os.path.join(os.path.dirname(__file__), "persuasion_taxonomy.jsonl")) as f:
    for line in f:
        technique = json.loads(line)
        technique = {k.replace("ss_", ""): v for k, v in technique.items()}
        TAXONOMY.append(technique)


class TherapyActionSpace(ActionSpace):
    def __init__(self, strategy_idx="random"):
        self.strategy_idx = strategy_idx

    def sample(self) -> Action:
        if self.strategy_idx == "random":
            return TherapyAction()
        else:
            return TherapyAction(persuasion_technique=self.strategy_idx)

    def __str__(self) -> str:
        if self.strategy_idx == "random":
            return "Random"
        elif self.strategy_idx < 0:
            return "None"
        else:
            return TAXONOMY[self.strategy_idx]["technique"]


class TherapyAction(Action):
    def __init__(self, persuasion_technique=None):
        if persuasion_technique is None:
            persuasion_technique = random.randint(0, len(TAXONOMY) - 1)
        self.strategy = TAXONOMY[persuasion_technique] if persuasion_technique >= 0 else None

    def __call__(
        self,
        message: str,
        persona: dict,
        conversation: list,
        persuasion_flag: bool,
        words_limit: int,
    ) -> str:
        """
        Return the user-turn prompt that will be appended to the therapist's
        conversation history.

        All session instructions now live in the therapist's system prompt
        (see prompts.py), so the per-turn message is simply the patient's
        raw words.  The persuasion_flag and words_limit arguments are kept
        for interface compatibility but are no longer needed here.
        """
        return build_user_prompt(message)
