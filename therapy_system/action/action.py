from enum import Enum

class ActionType(Enum):
    NONE = 0
    
    def __str__(self) -> str:
        return f"ActionType.{self.name}"
    
class Action:
    def __init__(self):
        pass

    def __call__(self, 
                 message: str) -> str:
        return message
    
class ActionSpace:
    def __init__(self):
        pass

    def sample(self) -> Action:
        return Action()