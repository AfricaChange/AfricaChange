from providers.registry import ProviderRegistry


class ProviderFactory:
    @staticmethod
    def create(name: str, **kwargs):
        provider_cls = ProviderRegistry.get(name)
        return provider_cls(**kwargs)
