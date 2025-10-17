"""
ResumeMindAI CLI - Entry Point
AI-powered resume analysis and optimization tool
"""

import asyncio

from resumemind.core.cli import CLIInterface, CommandHandler
from resumemind.core.utils import DisplayManager


class ResumeMindApp:
    """Main application class"""

    def __init__(self):
        self.cli = CLIInterface()
        self.commands = CommandHandler()
        self.display = DisplayManager()

    async def run(self):
        """Main application entry point"""
        # Display welcome message
        self.display.show_welcome()

        # Provider selection flow
        provider_type = self.cli.select_provider_type()
        config, litellm_config = self.cli.select_model(provider_type)

        if not config:
            self.display.print("[red]No provider selected. Exiting.[/red]")
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
