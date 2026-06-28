class ProviderRegistry:
    _providers = {}

    @classmethod
    def register(cls, provider_cls):
        name = getattr(provider_cls, "provider_name", None)
        if not name:
            raise ValueError("Provider sans provider_name")
        cls._providers[name] = provider_cls
        return provider_cls

    @classmethod
    def get(cls, name: str):
        if name not in cls._providers:
            raise KeyError(f"Provider inconnu: {name}")
        return cls._providers[name]

    @classmethod
    def list_names(cls):
        return sorted(cls._providers.keys())
