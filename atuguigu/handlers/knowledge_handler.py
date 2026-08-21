from domain.state import DialogueState
from planner.intents import KnowledgeIntent


class KnowledgeHandler:

    def __init__(self,intents:dict[str,KnowledgeIntent]):
        self.intents = intents

    async def handle(self,intents:list[str],dialogue_state:DialogueState):
        pass