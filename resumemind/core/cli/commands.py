"""
Command handlers for the CLI application
"""

from pathlib import Path
from typing import Any, Dict, Optional

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
        if not self.current_resume_path or not self.analysis_options:
            self.display.print("[red]Missing resume file or analysis options.[/red]")
            return

        self.display.print(
            "\n[bold yellow]🔄 Starting Resume Analysis...[/bold yellow]"
        )

        try:
            # Simulate analysis steps
            import asyncio

            self.display.print("[dim]📖 Reading resume file...[/dim]")
            await asyncio.sleep(1)

            self.display.print("[dim]🧠 Analyzing content with AI...[/dim]")
            await asyncio.sleep(2)

            self.display.print("[dim]📊 Generating insights...[/dim]")
            await asyncio.sleep(1)

            # Show results placeholder
            self.display.print("\n[bold green]✅ Analysis Complete![/bold green]")
            self.display.print("\n[bold cyan]📋 Resume Analysis Results[/bold cyan]")

            # Mock results based on selected options
            self.display.print(
                f"\n[bold]Analysis Type:[/bold] {self.analysis_options['analysis_depth']}"
            )

            for area in self.analysis_options["focus_areas"]:
                self.display.print(f"\n[bold yellow]{area}:[/bold yellow]")
                self.display.print("[dim]• Analysis results would appear here[/dim]")
                self.display.print("[dim]• Recommendations and improvements[/dim]")
                self.display.print("[dim]• Specific actionable feedback[/dim]")

            if "target_role" in self.analysis_options:
                self.display.print(
                    f"\n[bold yellow]Role-Specific Feedback for '{self.analysis_options['target_role']}':[/bold yellow]"
                )
                self.display.print(
                    "[dim]• Tailored recommendations for this role[/dim]"
                )
                self.display.print("[dim]• Missing keywords and skills[/dim]")
                self.display.print("[dim]• Industry-specific suggestions[/dim]")

            self.display.print(
                "\n[green]💡 This is a preview. Full AI analysis will be implemented with the selected LLM provider.[/green]"
            )

        except Exception as e:
            self.display.print(f"\n[red]Analysis failed: {str(e)}[/red]")

        input("\nPress Enter to return to main menu...")
