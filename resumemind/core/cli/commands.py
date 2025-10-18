"""
Command handlers for the CLI application
"""

from pathlib import Path
from typing import Any, Dict, Optional

from resumemind.core.services.resume_ingestion_service import (
    process_resume_content,
    read_resume,
)

from ..providers import ProviderConfig
from ..utils import DisplayManager
from .interface import CLIInterface


class CommandHandler:
    """Handles application commands and business logic"""

    def __init__(self):
        self.display = DisplayManager()
        self.interface = CLIInterface()
        self.selected_provider: Optional[ProviderConfig] = None
        self.litellm_config: Optional[dict] = None
        self.current_resume_path: Optional[str] = None
        self.analysis_options: Optional[Dict[str, Any]] = None

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

        # Start main application loop
        await self.run_main_loop()

    async def run_main_loop(self):
        """Main application loop with menu system"""
        while True:
            try:
                choice = self.interface.show_main_menu()

                if choice == "1":
                    await self.handle_resume_ingestion()
                elif choice == "2":
                    self.display.print(
                        "\n[yellow]Provider change requested. Please restart the application.[/yellow]"
                    )
                    return
                elif choice == "3":
                    self.display.print(
                        "\n[bold cyan]Thank you for using ResumeMindAI! 👋[/bold cyan]"
                    )
                    return

            except KeyboardInterrupt:
                self.display.print("\n\n[yellow]Operation cancelled by user.[/yellow]")
                if self.interface.display.print and hasattr(self.interface, "display"):
                    from rich.prompt import Confirm

                    if not Confirm.ask(
                        "Would you like to return to the main menu?", default=True
                    ):
                        return
                else:
                    return
            except Exception as e:
                self.display.print(f"\n[red]An error occurred: {str(e)}[/red]")
                self.display.print("[dim]Returning to main menu...[/dim]")

    async def handle_resume_ingestion(self):
        """Handle resume ingestion workflow"""
        self.display.print("\n[bold cyan]📄 Resume Ingestion[/bold cyan]")

        # Get resume file
        resume_path = self.interface.get_resume_file_path()
        if not resume_path:
            self.display.print("[yellow]Resume ingestion cancelled.[/yellow]")
            return

        self.current_resume_path = resume_path

        # Show summary and confirm
        self.display.print("\n[bold green]📋 Ingestion Summary[/bold green]")
        self.display.print(f"[dim]Resume: {Path(resume_path).name}[/dim]")

        from rich.prompt import Confirm

        if Confirm.ask("\nProceed with ingestion?", default=True):
            await self.run_resume_ingestion()
        else:
            self.display.print("[yellow]Ingestion cancelled.[/yellow]")

    async def run_resume_ingestion(self):
        """Main resume analysis functionality"""
        if not self.current_resume_path:
            self.display.print("[red]Missing resume file or analysis options.[/red]")
            return

        self.display.print("\n[bold yellow]🔄 Ingesting Your Resume...[/bold yellow]")

        try:
            # Simulate analysis steps
            import asyncio

            self.display.print("[dim]📖 Reading resume file...[/dim]")
            self.current_resume_content = await read_resume(self.current_resume_path)

            self.display.print("[dim]🪄 Cleaning up your resume...[/dim]")
            self.processed_resume_content = await process_resume_content(
                self.current_resume_content
            )

            self.display.print("[dim]🧠 Analyzing content with AI...[/dim]")
            await asyncio.sleep(2)

            self.display.print("[dim]📊 Ingesting content to GraphDB...[/dim]")
            await asyncio.sleep(1)

            # Show results
            self.display.print(
                "\n[bold green]✅ Resume Ingestion Complete![/bold green]"
            )

        except Exception as e:
            self.display.print(f"\n[red]Ingestion failed: {str(e)}[/red]")

        input("\nPress Enter to return to main menu...")
