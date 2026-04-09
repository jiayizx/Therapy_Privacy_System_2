from therapy_system.agents.llms.lm_model import LM_Agent


def load_llm_agent(model_name, args):
    if "human" in model_name.lower():
        from therapy_system.agents.human import HumanAgent
        return HumanAgent()
    elif "openai" in model_name.lower() or "gpt" in model_name.lower():
        from therapy_system.agents.llms.openai import OpenAIAgent
        return OpenAIAgent(model_name, **args)
    else:
        from therapy_system.agents.llms.openrouter import OpenRouterAgent
        return OpenRouterAgent(model_name, **args)
