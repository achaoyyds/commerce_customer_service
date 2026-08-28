from atuguigu.handlers.providers.base import Provider


class ProviderRegister:

    def __init__(self,providers:list[Provider]):
        self._provider = {provider.provider_id:provider for provider in providers}


    def get_provider(self,provider_id:str) -> Provider:
        return self._provider[provider_id]