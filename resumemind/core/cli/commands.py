"""
Command handlers for the CLI application
"""

from typing import Optional

from ..providers import ProviderConfig
from ..utils import DisplayManager


class CommandHandler:
    """Handles application commands and business logic"""

    def __init__(self):
        self.display = DisplayManager()
        self.selected_provider: Optional[ProviderConfig] = None
        self.litellm_config: Optional[dict] = None

    def set_provider_config(self, provider: ProviderConfig, litellm_config: dict):
        """Set the selected provider configuration"""
        self.selected_provider = provider
        self.litellm_config = litellm_config

    def show_configuration(self):
        """Display the current configuration"""
        if self.selected_provider:
            self.display.show_selected_config(self.selected_provider)

    async def start_application(self):
        """Start the main application with selected provider"""
        if not self.selected_provider or not self.litellm_config:
            self.display.print("[red]No provider configuration available.[/red]")
            return

        self.display.print(
            "\n[bold green]Configuration complete! Starting ResumeMindAI...[/bold green]"
        )

        # Display startup information
        self.display.print(f"[dim]Starting with {self.selected_provider.name}...[/dim]")
        self.display.print(f"[dim]LiteLLM Config: {self.litellm_config}[/dim]")

        # This is where you would integrate with your actual application logic
        # For now, just show that the configuration is ready
        self.display.print(
            "[green]✅ Application ready with selected LLM provider![/green]"
        )

        # TODO: Add your main application logic here
        # await self.run_resume_analysis()

    async def run_resume_analysis(self):
        """Main resume analysis functionality (placeholder)"""
        # This is where you would implement the core resume analysis features
        # using the configured LLM provider
        pass
