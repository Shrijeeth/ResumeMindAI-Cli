"""
CLI interface for provider selection and configuration
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from rich.prompt import Confirm, Prompt

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
            "\nSelect a provider type", choices=["1", "2", "3", "4"], default="1"
        )

        provider_type_map = {
            "1": ProviderType.GPT,
            "2": ProviderType.GEMINI,
            "3": ProviderType.CLAUDE,
            "4": ProviderType.LITELLM,  # LiteLLM - unified LLM interface library
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

    def show_main_menu(self) -> str:
        """Display main application menu and get user choice"""
        self.display.print("\n[bold cyan]🎯 ResumeMindAI - Main Menu[/bold cyan]")
        self.display.print("[dim]Choose what you'd like to do:[/dim]\n")

        menu_options = {
            "1": "📄 Resume Ingestion",
            "2": "⚙️ Change LLM Provider",
            "3": "❌ Exit",
        }

        for key, value in menu_options.items():
            self.display.print(f"  {key}. {value}")

        choice = Prompt.ask(
            "\nSelect an option", choices=list(menu_options.keys()), default="1"
        )

        return choice

    def get_resume_file_path(self) -> Optional[str]:
        """Get resume file path from user with validation"""
        self.display.print("\n[bold yellow]📄 Resume File Selection[/bold yellow]")
        self.display.print("[dim]Please provide your resume file for analysis.[/dim]\n")

        supported_formats = [".pdf", ".docx", ".doc", ".txt"]
        self.display.print(
            f"[dim]Supported formats: {', '.join(supported_formats)}[/dim]"
        )

        while True:
            file_path = Prompt.ask("Enter the path to your resume file", default="")

            if not file_path.strip():
                if not Confirm.ask(
                    "No file path provided. Would you like to try again?"
                ):
                    return None
                continue

            # Expand user path and resolve
            expanded_path = os.path.expanduser(file_path.strip())
            resolved_path = Path(expanded_path).resolve()

            # Validate file exists
            if not resolved_path.exists():
                self.display.print(f"[red]❌ File not found: {resolved_path}[/red]")
                if not Confirm.ask("Would you like to try a different path?"):
                    return None
                continue

            # Validate file is actually a file
            if not resolved_path.is_file():
                self.display.print(f"[red]❌ Path is not a file: {resolved_path}[/red]")
                if not Confirm.ask("Would you like to try a different path?"):
                    return None
                continue

            # Validate file format
            file_extension = resolved_path.suffix.lower()
            if file_extension not in supported_formats:
                self.display.print(
                    f"[yellow]⚠️  Unsupported file format: {file_extension}[/yellow]"
                )
                self.display.print(
                    f"[dim]Supported formats: {', '.join(supported_formats)}[/dim]"
                )
                if not Confirm.ask("Would you like to proceed anyway?"):
                    if not Confirm.ask("Would you like to try a different file?"):
                        return None
                    continue

            # File validation passed
            self.display.print(
                f"[green]✅ Resume file selected: {resolved_path.name}[/green]"
            )
            self.display.print(f"[dim]Full path: {resolved_path}[/dim]")

            return str(resolved_path)

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
