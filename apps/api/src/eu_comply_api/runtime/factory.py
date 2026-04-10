from eu_comply_api.config import Settings
from eu_comply_api.domain.models import ProviderKind
from eu_comply_api.runtime.ollama import OllamaAdapter
from eu_comply_api.runtime.openrouter import OpenRouterAdapter


def build_runtime_adapter(
    provider: ProviderKind,
    settings: Settings,
) -> OpenRouterAdapter | OllamaAdapter:
    if provider == ProviderKind.OPENROUTER:
        return OpenRouterAdapter(settings)
    return OllamaAdapter(settings)
