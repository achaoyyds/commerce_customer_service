from task.action.base import Action


class ActionRegister:
    """
    action的注册中心
    """

    def __init__(self):
        self._actions: dict[str, Action] = {}

    def register_action(self, action: Action):
        self._actions[action.name] = action

    def get_action(self, action_name: str) -> Action:
        return self._actions[action_name]