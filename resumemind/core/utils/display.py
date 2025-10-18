"""
Display utilities for rich terminal output
"""

from rich.console import Console
from rich.panel import Panel

from ..providers import ProviderConfig


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
