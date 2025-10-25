"""
Command handlers for the CLI application
"""

from pathlib import Path
from typing import Any, Dict, Optional

from resumemind.core.services.resume_ingestion_service import (
    complete_resume_ingestion_workflow_with_human_review,
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
                    self.handle_view_resumes()
                elif choice == "3":
                    await self.handle_resume_optimization()
                elif choice == "4":
                    await self.handle_resume_qa()
                elif choice == "5":
                    await self.handle_provider_management()
                elif choice == "6":
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
            # Use the complete workflow
            self.display.print(
                "[dim]🚀 Starting complete resume ingestion workflow...[/dim]"
            )

            workflow_result = (
                await complete_resume_ingestion_workflow_with_human_review(
                    self.current_resume_path,
                    self.selected_provider,
                    self.interface,
                )
            )

            if workflow_result["success"]:
                # Display detailed results
                self.display.print(
                    f"[dim]📄 Resume ID: {workflow_result['resume_id']}[/dim]"
                )
                self.display.print(
                    f"[dim]📊 Extracted {workflow_result['triplet_count']} relationships[/dim]"
                )
                self.display.print(
                    f"[dim]🏷️  Identified {workflow_result['entity_count']} entities[/dim]"
                )

                if workflow_result["graph_stored"]:
                    self.display.print(
                        "[dim]💾 Successfully stored in graph database[/dim]"
                    )
                else:
                    self.display.print("[dim]⚠️  Graph database storage failed[/dim]")

                # Store results for potential future use
                self.workflow_result = workflow_result

                # Show completion message
                self.display.print(
                    "\n[bold green]✅ Resume Ingestion Complete![/bold green]"
                )

                # Display some sample entities and relationships
                self._display_graph_summary(workflow_result)

            else:
                # Check if user cancelled during review
                if workflow_result.get("user_cancelled"):
                    self.display.print(
                        "\n[yellow]Resume ingestion was cancelled during the review process.[/yellow]"
                    )
                else:
                    self.display.print(
                        f"\n[red]Workflow failed: {workflow_result.get('error', 'Unknown error')}[/red]"
                    )

        except Exception as e:
            self.display.print(f"\n[red]Ingestion failed: {str(e)}[/red]")

        input("\nPress Enter to return to main menu...")

    def _display_graph_summary(self, workflow_result: dict):
        """Display a summary of the extracted graph data"""
        if not workflow_result.get("graph_data"):
            return

        graph_data = workflow_result["graph_data"]

        # Display sample entities by type
        self.display.print("\n[bold]📊 Graph Summary:[/bold]")

        # Group entities by type (extracted from triplets)
        entities_by_type = {}
        for triplet in graph_data.triplets:
            # Add subject entity
            if triplet.subject_type not in entities_by_type:
                entities_by_type[triplet.subject_type] = []
            if triplet.subject not in entities_by_type[triplet.subject_type]:
                entities_by_type[triplet.subject_type].append(triplet.subject)

            # Add object entity
            if triplet.object_type not in entities_by_type:
                entities_by_type[triplet.object_type] = []
            if triplet.object not in entities_by_type[triplet.object_type]:
                entities_by_type[triplet.object_type].append(triplet.object)

        # Display top entity types
        for entity_type, entities in list(entities_by_type.items())[:5]:
            entity_list = ", ".join(entities[:3])
            if len(entities) > 3:
                entity_list += f" (+{len(entities) - 3} more)"
            self.display.print(f"[dim]• {entity_type}: {entity_list}[/dim]")

        # Display sample relationships
        if graph_data.triplets:
            self.display.print("\n[bold]🔗 Sample Relationships:[/bold]")
            for triplet in graph_data.triplets[:3]:
                self.display.print(
                    f"[dim]• {triplet.subject} → {triplet.predicate} → {triplet.object}[/dim]"
                )

            if len(graph_data.triplets) > 3:
                self.display.print(
                    f"[dim]• ... and {len(graph_data.triplets) - 3} more relationships[/dim]"
                )

    def handle_view_resumes(self):
        """Handle viewing ingested resumes"""
        self.interface.display_ingested_resumes()

    async def handle_provider_management(self):
        """Handle provider management workflow"""

        result = self.interface.show_provider_management_menu()
        if result:
            config, litellm_config = result
            self.set_provider_config(config, litellm_config)
            self.display.print(f"\n[green]✅ Provider updated: {config.name}[/green]")
        else:
            self.display.print("\n[yellow]Provider management cancelled.[/yellow]")

    async def handle_resume_optimization(self):
        """Handle resume optimization workflow"""
        from ..services.resume_optimization_service import ResumeOptimizationService

        # Select resume
        resume_id = await self.interface.select_resume_for_optimization()
        if not resume_id:
            return

        # Get additional context
        additional_context = self.interface.get_optimization_context()

        # Show progress
        self.display.print("\n[bold yellow]🔄 Analyzing Resume...[/bold yellow]")
        self.display.print("[dim]This may take a moment...[/dim]\n")

        try:
            # Create optimization service
            optimization_service = ResumeOptimizationService(
                model_id=self.selected_provider.model,
                api_key=self.selected_provider.api_key_env,
                base_url=self.selected_provider.base_url,
                additional_params=self.selected_provider.additional_params or {},
            )

            # Run optimization
            optimization_result = await optimization_service.optimize_resume(
                resume_id=resume_id,
                additional_context=additional_context,
            )

            if optimization_result:
                # Display results
                self.interface.display_optimization_results(optimization_result)
                self.display.print("[green]✅ Resume optimization complete![/green]")
            else:
                self.display.print(
                    "[red]❌ Failed to optimize resume. Please try again.[/red]"
                )

        except Exception as e:
            self.display.print(f"\n[red]Error during optimization: {str(e)}[/red]")
            self.display.print(
                "[dim]Please check your provider configuration and try again.[/dim]"
            )

    async def handle_resume_qa(self):
        """Handle resume Q&A workflow"""
        while True:
            choice = self.interface.show_qa_menu()

            if choice == "1":
                await self._handle_specific_resume_qa()
            elif choice == "2":
                await self._handle_general_qa()
            elif choice == "3":
                return

    async def _handle_specific_resume_qa(self):
        """Handle Q&A chat for a specific resume"""
        try:
            # Select resume first
            resume_id = await self.interface.select_resume_for_optimization()
            if not resume_id:
                return

            # Create embedding service and QA service
            from ..services.embedding_service import (
                create_embedding_service_from_provider,
            )
            from ..services.resume_qa_service import ResumeQAService

            embedding_service = create_embedding_service_from_provider(
                self.selected_provider
            )

            qa_service = ResumeQAService(
                model_id=self.selected_provider.model,
                api_key=self.selected_provider.api_key_env,
                base_url=self.selected_provider.base_url,
                additional_params=self.selected_provider.additional_params or {},
                embedding_service=embedding_service,
            )

            # Start chat session
            self.display.print("\n[bold cyan]💬 Chat Mode - Resume Q&A[/bold cyan]")
            self.display.print(
                "[dim]Ask questions about this resume. Type 'exit' to end, 'clear' to clear history.[/dim]"
            )

            chat_number = 1
            while True:
                # Get question
                question = self.interface.ask_chat_question(chat_number)

                if not question:
                    continue

                if question.lower() == "exit":
                    self.display.print("\n[green]👋 Ending chat session[/green]")
                    break

                if question.lower() == "clear":
                    qa_service.clear_chat_history()
                    self.display.print("\n[green]✅ Chat history cleared[/green]")
                    chat_number = 1
                    continue

                # Get answer
                self.display.print("\n[dim]🔄 Thinking...[/dim]")
                answer = await qa_service.ask_question(
                    resume_id=resume_id,
                    question=question,
                )

                if answer:
                    self.display.print("\n[bold green]AI:[/bold green]")
                    self.display.print(answer)
                else:
                    self.display.print("[red]❌ Failed to get answer.[/red]")

                chat_number += 1

        except Exception as e:
            self.display.print(f"\n[red]Error during Q&A: {str(e)}[/red]")
            self.display.print(
                "[dim]Please check your provider configuration and try again.[/dim]"
            )

    async def _handle_general_qa(self):
        """Handle Q&A chat across all resumes"""
        try:
            # Create embedding service and QA service
            from ..services.embedding_service import (
                create_embedding_service_from_provider,
            )
            from ..services.resume_qa_service import ResumeQAService

            embedding_service = create_embedding_service_from_provider(
                self.selected_provider
            )

            qa_service = ResumeQAService(
                model_id=self.selected_provider.model,
                api_key=self.selected_provider.api_key_env,
                base_url=self.selected_provider.base_url,
                additional_params=self.selected_provider.additional_params or {},
                embedding_service=embedding_service,
            )

            # Start chat session
            self.display.print(
                "\n[bold cyan]💬 Chat Mode - Search All Resumes[/bold cyan]"
            )
            self.display.print(
                "[dim]Ask questions across all resumes. Type 'exit' to end, 'clear' to clear history.[/dim]"
            )

            chat_number = 1
            while True:
                # Get question
                question = self.interface.ask_chat_question(chat_number)

                if not question:
                    continue

                if question.lower() == "exit":
                    self.display.print("\n[green]👋 Ending chat session[/green]")
                    break

                if question.lower() == "clear":
                    qa_service.clear_chat_history()
                    self.display.print("\n[green]✅ Chat history cleared[/green]")
                    chat_number = 1
                    continue

                # Get answer
                self.display.print("\n[dim]🔄 Searching...[/dim]")
                answer = await qa_service.ask_question_all_resumes(question=question)

                if answer:
                    self.display.print("\n[bold green]AI:[/bold green]")
                    self.display.print(answer)
                else:
                    self.display.print("[red]❌ Failed to get answer.[/red]")

                chat_number += 1

        except Exception as e:
            self.display.print(f"\n[red]Error during Q&A: {str(e)}[/red]")
            self.display.print(
                "[dim]Please check your provider configuration and try again.[/dim]"
            )
