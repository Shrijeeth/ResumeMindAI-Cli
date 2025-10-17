"""
CLI interface for provider selection and configuration
"""

from typing import Optional, Tuple

from rich.prompt import Prompt

from ..providers import LLMProviders, ProviderConfig, ProviderType
from ..utils import DisplayManager


class CLIInterface:
    """Handles CLI interactions for provider selection"""

    def __init__(self):
        self.display = DisplayManager()

    def select_provider_type(self) -> ProviderType:
        """Let user select provider type"""
        self.display.show_provider_types()

        choice = Prompt.ask(
            "\nSelect a provider type", choices=["1", "2", "3", "4", "5"], default="1"
        )

        provider_type_map = {
            "1": ProviderType.GPT,
            "2": ProviderType.GEMINI,
            "3": ProviderType.CLAUDE,
            "4": ProviderType.OLLAMA,
            "5": ProviderType.LITELLM,
        }

        return provider_type_map[choice]

    def get_custom_litellm_config(self) -> Tuple[ProviderConfig, dict]:
        """Get custom LiteLLM configuration from user"""
        self.display.print("\n[bold yellow]Custom LiteLLM Configuration[/bold yellow]")

        model = Prompt.ask("Enter model name (e.g., 'gpt-4', 'claude-3-opus-20240229')")
        api_key = Prompt.ask(
            "Enter API key (optional, press Enter to skip)", default=""
        )
        base_url = Prompt.ask(
            "Enter base URL (optional, press Enter to skip)", default=""
        )

        config = ProviderConfig(
            name=f"Custom {model}",
            provider_type=ProviderType.LITELLM,
            model=model,
            base_url=base_url if base_url else None,
        )

        # Create LiteLLM config
        litellm_config = {"model": model}
        if api_key:
            litellm_config["api_key"] = api_key
        if base_url:
            litellm_config["api_base"] = base_url

        return config, litellm_config

    def select_model(
        self, provider_type: ProviderType
    ) -> Tuple[Optional[ProviderConfig], Optional[dict]]:
        """Let user select specific model"""
        if provider_type == ProviderType.LITELLM:
            return self.get_custom_litellm_config()

        providers = LLMProviders.get_providers_by_type(provider_type)
        model_options = self.display.show_models_for_type(provider_type, providers)

        if not model_options:
            return None, None

        choice = Prompt.ask(
            f"\nSelect a {provider_type.value} model",
            choices=list(model_options.keys()),
            default="1",
        )

        key, config = model_options[choice]

        # Prompt for API key if needed
        if config.api_key_env:
            api_key = Prompt.ask(
                f"Enter your {config.api_key_env.replace('_', ' ').title()}",
                password=True,
            )
            if not api_key.strip():
                self.display.print("[red]API key is required for this provider.[/red]")
                return None, None
        else:
            api_key = None

        # Create LiteLLM config
        litellm_config = {"model": config.model}
        if api_key:
            litellm_config["api_key"] = api_key
        if config.base_url:
            litellm_config["api_base"] = config.base_url
        if config.additional_params:
            litellm_config.update(config.additional_params)

        return config, litellm_config
