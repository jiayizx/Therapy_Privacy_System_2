from therapy_system.agents import Agent

class HumanAgent(Agent):
    def __init__(self):
        pass

    def chat(self, message) -> str:
        return message