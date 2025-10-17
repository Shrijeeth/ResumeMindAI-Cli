"""
Display utilities for rich terminal output
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..providers import ProviderConfig, ProviderType


class DisplayManager:
    """Manages rich terminal display components"""

    def __init__(self):
        self.console = Console()

    def show_welcome(self):
        """Display welcome message"""
        welcome_text = """
[bold blue]Welcome to ResumeMindAI CLI[/bold blue]
[dim]AI-powered resume analysis and optimization[/dim]
        """
        self.console.print(Panel(welcome_text, expand=False))

    def show_provider_types(self):
        """Display available provider types"""
        table = Table(
            title="Available LLM Provider Types",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Option", style="cyan", no_wrap=True)
        table.add_column("Provider", style="green")
        table.add_column("Description", style="yellow")

        provider_info = {
            "1": ("OpenAI GPT", "GPT-4, GPT-3.5 Turbo models"),
            "2": ("Google Gemini", "Gemini Pro, Gemini 1.5 Pro models"),
            "3": ("Anthropic Claude", "Claude 3 Opus, Sonnet, Haiku models"),
            "4": ("Ollama", "Local models via Ollama"),
            "5": ("Custom LiteLLM", "Custom model configuration"),
        }

        for option, (provider, description) in provider_info.items():
            table.add_row(option, provider, description)

        self.console.print(table)

    def show_models_for_type(self, provider_type: ProviderType, providers: dict):
        """Display available models for a specific provider type"""
        if not providers:
            self.console.print("[red]No models available for this provider type.[/red]")
            return None

        table = Table(
            title=f"Available {provider_type.value.upper()} Models",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Option", style="cyan", no_wrap=True)
        table.add_column("Model", style="green")
        table.add_column("Type", style="yellow")

        model_options = {}
        for i, (key, config) in enumerate(providers.items(), 1):
            model_type = "API Key Required" if config.api_key_env else "Local/No Auth"
            table.add_row(str(i), config.name, model_type)
            model_options[str(i)] = (key, config)

        self.console.print(table)
        return model_options

    def show_selected_config(self, config: ProviderConfig):
        """Display the selected configuration"""
        config_text = f"""
[bold green]Selected Configuration:[/bold green]
[cyan]Provider:[/cyan] {config.name}
[cyan]Model:[/cyan] {config.model}
[cyan]Type:[/cyan] {config.provider_type.value}
        """

        if config.api_key_env:
            config_text += "\n[cyan]Authentication:[/cyan] API Key Provided"

        if config.base_url:
            config_text += f"\n[cyan]Base URL:[/cyan] {config.base_url}"

        self.console.print(Panel(config_text, expand=False))

    def print(self, *args, **kwargs):
        """Wrapper for console.print"""
        self.console.print(*args, **kwargs)
