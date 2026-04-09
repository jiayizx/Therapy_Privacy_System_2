from therapy_system.action import Action, ActionSpace

class HumanActionSpace(ActionSpace):
    def __init__(self):
        pass

    def sample(self) -> Action:
        return HumanAction()

class HumanAction(Action):
    def __init__(self):
        pass

    def __str__(self):
        return "Human-input"