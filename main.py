"""
ResumeMindAI CLI - Entry Point
AI-powered resume analysis and optimization tool
"""

import asyncio

from resumemind.core.cli import CLIInterface, CommandHandler
from resumemind.core.persistence import ProviderStateService
from resumemind.core.utils import DisplayManager


class ResumeMindApp:
    """Main application class"""

    def __init__(self):
        self.cli = CLIInterface()
        self.commands = CommandHandler()
        self.display = DisplayManager()
        self.state_service = ProviderStateService()

    async def run(self):
        """Main application entry point"""
        # Display welcome message
        self.display.show_welcome()

        # Check for active provider first
        active_provider = self.state_service.get_active_provider()
        config = None
        litellm_config = None

        if active_provider:
            self.display.print(
                f"\n[green]🔄 Loading active provider: {active_provider.name}[/green]"
            )
            result = self.state_service.get_provider_config_and_litellm(
                active_provider.id
            )
            if result:
                config, litellm_config = result
                self.display.print(f"[dim]Model: {config.model}[/dim]")

        # If no active provider or failed to load, use provider selection
        if not config:
            self.display.print(
                "\n[yellow]No active provider found. Let's set one up![/yellow]"
            )
            result = self.cli.select_model()
            if result:
                config, litellm_config = result

        if not config:
            self.display.print("[red]No model selected. Exiting.[/red]")
            return

        # Set configuration
        self.commands.set_provider_config(config, litellm_config)

        # Display selected configuration
        self.commands.show_configuration()

        # Start the main application
        await self.commands.start_application()


async def main():
    """Application entry point"""
    app = ResumeMindApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
