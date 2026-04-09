from therapy_system.envs.alternating_conv import Turn, AlternatingConv
from therapy_system.envs.conversation import Conv
from therapy_system.envs.therapy import Therapy

def make(env_name, **kwargs) -> Conv:
    '''
    Defining the environment
    '''
    if env_name == "Therapy":
        return Therapy(**kwargs)
    else:
        raise NotImplementedError(f"Environment {env_name} not found")