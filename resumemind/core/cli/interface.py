"""
CLI interface for provider selection and configuration
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..persistence.resume_storage_service import ResumeStorageService
from ..providers import LLMProviders, ProviderConfig
from ..providers.manager import ProviderManager
from ..utils import DisplayManager


class CLIInterface:
    """Handles CLI interactions for provider selection"""

    def __init__(self):
        self.display = DisplayManager()
        self.provider_manager = ProviderManager()

    def select_model(self) -> Tuple[Optional[ProviderConfig], Optional[dict]]:
        """Select or configure a LiteLLM model using the provider manager"""
        return self.provider_manager.get_or_create_provider()

    def get_custom_model_config(self) -> Tuple[ProviderConfig, dict]:
        """Get custom model configuration from user with embedding support"""
        self.display.print("\n[bold cyan]🤖 LiteLLM Model Configuration[/bold cyan]")
        self.display.print(
            "[dim]Configure any model supported by LiteLLM. Examples:[/dim]"
        )
        self.display.print("[dim]• OpenAI: gpt-4o, gpt-4, gpt-3.5-turbo[/dim]")
        self.display.print(
            "[dim]• Anthropic: claude-3-5-sonnet-20241022, claude-3-opus-20240229[/dim]"
        )
        self.display.print(
            "[dim]• Google: gemini/gemini-1.5-pro, gemini/gemini-pro[/dim]"
        )
        self.display.print("[dim]• Ollama: ollama/llama3.2, ollama/mistral[/dim]")
        self.display.print(
            "[dim]• And many more providers supported by LiteLLM[/dim]\n"
        )

        # LLM Configuration
        model = Prompt.ask("Enter model name")
        api_key = Prompt.ask(
            "Enter API key (optional for local models like Ollama)", default=""
        )
        base_url = Prompt.ask(
            "Enter base URL (optional, e.g., http://localhost:11434 for Ollama)",
            default="",
        )

        # Embedding Configuration
        self.display.print("\n[bold cyan]🔍 Embedding Configuration[/bold cyan]")
        self.display.print(
            "[dim]Configure embedding model for GraphRAG support. Examples:[/dim]"
        )
        self.display.print(
            "[dim]• OpenAI: text-embedding-3-small, text-embedding-3-large[/dim]"
        )
        self.display.print(
            "[dim]• Ollama: ollama/nomic-embed-text, ollama/mxbai-embed-large[/dim]"
        )
        self.display.print("[dim]• Google: text-embedding-004[/dim]")
        self.display.print(
            "[dim]• Leave empty for auto-selection based on your LLM model[/dim]\n"
        )

        embedding_model = Prompt.ask("Enter embedding model (optional)", default="")
        embedding_api_key = Prompt.ask(
            "Enter embedding API key (optional, will use LLM key if empty)", default=""
        )
        embedding_base_url = Prompt.ask(
            "Enter embedding base URL (optional, will use LLM URL if empty)", default=""
        )

        return LLMProviders.create_custom_config(
            model=model,
            api_key=api_key if api_key else None,
            base_url=base_url if base_url else None,
            embedding_model=embedding_model if embedding_model else None,
            embedding_api_key=embedding_api_key if embedding_api_key else None,
            embedding_base_url=embedding_base_url if embedding_base_url else None,
        )

    def show_main_menu(self) -> str:
        """Display main application menu and get user choice"""
        self.display.print("\n[bold cyan]🎯 ResumeMindAI - Main Menu[/bold cyan]")
        self.display.print("[dim]Choose what you'd like to do:[/dim]\n")

        menu_options = {
            "1": "📄 Resume Ingestion",
            "2": "📚 View Ingested Resumes",
            "3": "✨ Resume Optimizer",
            "4": "💬 Ask Questions (Q&A)",
            "5": "🤖 Manage Providers",
            "6": "❌ Exit",
        }

        for key, value in menu_options.items():
            self.display.print(f"  {key}. {value}")

        choice = Prompt.ask(
            "\nSelect an option", choices=list(menu_options.keys()), default="1"
        )

        return choice

    def show_provider_management_menu(self) -> Optional[Tuple[ProviderConfig, dict]]:
        """Show provider management interface"""
        return self.provider_manager.get_or_create_provider()

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

    async def review_extracted_triplets(
        self, graph_data, formatted_resume=None, graph_extractor=None
    ) -> bool:
        """
        Display extracted triplets to user for review and allow modifications.

        Args:
            graph_data: ResumeGraphExtractionOutput containing triplets

        Returns:
            True if user approves the triplets, False to cancel ingestion
        """
        self.display.print(
            "\n[bold cyan]🔍 Triplet Review - Human in the Loop[/bold cyan]"
        )
        self.display.print(
            "[dim]Please review the extracted relationships from your resume.[/dim]\n"
        )

        # Display triplets in a table
        self._display_triplets_table(graph_data.triplets)

        # Show summary statistics
        self._display_triplet_summary(graph_data)

        # Main review menu
        while True:
            self.display.print("\n[bold yellow]Review Options:[/bold yellow]")
            self.display.print("  1. ✅ Approve and continue with ingestion")
            self.display.print("  2. 📝 Add specific information to look for")
            self.display.print("  3. 🗑️  Remove specific triplets")
            self.display.print("  4. 👀 View detailed triplet information")
            self.display.print("  5. ❌ Cancel ingestion")

            choice = Prompt.ask(
                "\nSelect an option", choices=["1", "2", "3", "4", "5"], default="1"
            )

            if choice == "1":
                # Check if there are additional extraction requests to process
                if (
                    graph_data.additional_extraction_requests
                    and formatted_resume
                    and graph_extractor
                ):
                    self.display.print(
                        "\n[yellow]🔄 Processing additional extraction requests...[/yellow]"
                    )

                    try:
                        # Extract additional triplets based on user requests
                        additional_triplets = (
                            await graph_extractor.extract_additional_triplets(
                                formatted_resume,
                                graph_data.additional_extraction_requests,
                            )
                        )

                        if additional_triplets:
                            # Create a set of existing triplet signatures for deduplication
                            existing_signatures = set()
                            for triplet in graph_data.triplets:
                                signature = f"{triplet.subject}|{triplet.predicate}|{triplet.object}"
                                existing_signatures.add(signature)

                            # Filter out duplicates from additional triplets
                            unique_additional = []
                            for triplet in additional_triplets:
                                signature = f"{triplet.subject}|{triplet.predicate}|{triplet.object}"
                                if signature not in existing_signatures:
                                    unique_additional.append(triplet)
                                    existing_signatures.add(signature)

                            # Append only unique triplets
                            graph_data.triplets.extend(unique_additional)
                            added_count = len(unique_additional)

                            if added_count > 0:
                                self.display.print(
                                    f"[green]✅ Added {added_count} new unique triplets![/green]"
                                )
                                if len(additional_triplets) > added_count:
                                    duplicates_filtered = (
                                        len(additional_triplets) - added_count
                                    )
                                    self.display.print(
                                        f"[yellow]📝 Filtered out {duplicates_filtered} duplicate triplets[/yellow]"
                                    )

                                # Show the new unique triplets to user
                                self.display.print(
                                    "\n[bold cyan]🆕 Newly Added Triplets:[/bold cyan]"
                                )
                                self._display_triplets_table(unique_additional)
                            else:
                                self.display.print(
                                    "[yellow]📝 All extracted triplets were duplicates - no new information added[/yellow]"
                                )

                            # Clear the requests since they've been processed
                            graph_data.additional_extraction_requests.clear()

                            # Continue the review loop with updated triplets
                            self.display.print(
                                "\n[yellow]Please review the updated triplet set...[/yellow]"
                            )

                            # Refresh the display with updated triplets
                            self.display.print(
                                "\n[bold cyan]🔄 Updated Complete Triplet Set:[/bold cyan]"
                            )
                            self._display_triplets_table(graph_data.triplets)
                            self._display_triplet_summary(graph_data)
                            continue
                        else:
                            self.display.print(
                                "[yellow]No additional information found for the requested topics.[/yellow]"
                            )
                            # Clear the requests even if no new triplets were found
                            graph_data.additional_extraction_requests.clear()

                    except Exception as e:
                        self.display.print(
                            f"[red]Error during additional extraction: {str(e)}[/red]"
                        )
                        self.display.print(
                            "[yellow]Continuing with current triplets...[/yellow]"
                        )
                        # Clear failed requests to avoid infinite loop
                        graph_data.additional_extraction_requests.clear()

                # Only approve if no additional requests are pending
                if not graph_data.additional_extraction_requests:
                    self.display.print(
                        "[green]✅ Triplets approved for ingestion![/green]"
                    )
                    return True
            elif choice == "2":
                self._handle_add_information_request(graph_data)
            elif choice == "3":
                self._handle_remove_triplets(graph_data)
            elif choice == "4":
                self._show_detailed_triplet_view(graph_data)
            elif choice == "5":
                if Confirm.ask("Are you sure you want to cancel the ingestion?"):
                    self.display.print("[yellow]Ingestion cancelled by user.[/yellow]")
                    return False

    def _display_triplets_table(self, triplets):
        """Display triplets in a formatted table"""
        table = Table(
            title="Extracted Graph Triplets",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Subject", style="cyan", width=20)
        table.add_column("Relationship", style="yellow", width=20)
        table.add_column("Object", style="green", width=20)
        table.add_column("Types", style="dim", width=15)

        for i, triplet in enumerate(triplets[:20], 1):  # Show first 20 triplets
            subject_type = (
                triplet.subject_type[:8] + "..."
                if len(triplet.subject_type) > 8
                else triplet.subject_type
            )
            object_type = (
                triplet.object_type[:8] + "..."
                if len(triplet.object_type) > 8
                else triplet.object_type
            )
            types_str = f"{subject_type} → {object_type}"

            table.add_row(
                str(i),
                triplet.subject[:18] + "..."
                if len(triplet.subject) > 18
                else triplet.subject,
                triplet.predicate[:18] + "..."
                if len(triplet.predicate) > 18
                else triplet.predicate,
                triplet.object[:18] + "..."
                if len(triplet.object) > 18
                else triplet.object,
                types_str,
            )

        self.display.print(table)

        if len(triplets) > 20:
            self.display.print(
                f"[dim]... and {len(triplets) - 20} more triplets (use option 4 to view all)[/dim]"
            )

    def _display_triplet_summary(self, graph_data):
        """Display summary statistics about the extracted triplets"""
        triplets = graph_data.triplets

        # Count entities by type
        entity_types = {}
        relationships = set()

        for triplet in triplets:
            # Count subject types
            entity_types[triplet.subject_type] = (
                entity_types.get(triplet.subject_type, 0) + 1
            )
            # Count object types (avoid double counting)
            if triplet.object_type != triplet.subject_type:
                entity_types[triplet.object_type] = (
                    entity_types.get(triplet.object_type, 0) + 1
                )
            # Collect relationship types
            relationships.add(triplet.predicate)

        self.display.print("\n[bold]📊 Summary:[/bold]")
        self.display.print(f"[dim]• Total triplets: {len(triplets)}[/dim]")
        self.display.print(
            f"[dim]• Unique relationship types: {len(relationships)}[/dim]"
        )
        self.display.print(f"[dim]• Entity types found: {len(entity_types)}[/dim]")

        # Show top entity types
        if entity_types:
            sorted_types = sorted(
                entity_types.items(), key=lambda x: x[1], reverse=True
            )
            self.display.print("[dim]• Top entity types:[/dim]")
            for entity_type, count in sorted_types[:5]:
                self.display.print(f"[dim]  - {entity_type}: {count}[/dim]")

    def _handle_add_information_request(self, graph_data):
        """Handle user request to specify additional information to extract"""
        self.display.print(
            "\n[bold yellow]📝 Additional Information Request[/bold yellow]"
        )
        self.display.print(
            "[dim]Specify what additional information should be looked for in the resume.[/dim]"
        )

        additional_info = Prompt.ask(
            "What specific information should be extracted? (e.g., 'certifications', 'volunteer work', 'publications')",
            default="",
        )

        if additional_info.strip():
            self.display.print(
                f"[green]✅ Added request to look for: {additional_info}[/green]"
            )
            self.display.print(
                "[dim]Note: This will be considered in future extractions. Current triplets remain unchanged.[/dim]"
            )
            # Store the additional info request for potential re-extraction
            graph_data.additional_extraction_requests.append(additional_info)
        else:
            self.display.print("[yellow]No additional information specified.[/yellow]")

    def _handle_remove_triplets(self, graph_data):
        """Handle user request to remove specific triplets"""
        self.display.print("\n[bold yellow]🗑️  Remove Triplets[/bold yellow]")
        self.display.print(
            "[dim]Specify triplets to remove by their number (from the table above).[/dim]"
        )

        if not graph_data.triplets:
            self.display.print("[yellow]No triplets to remove.[/yellow]")
            return

        # Show numbered list of triplets for easy reference
        self.display.print("\n[bold]Current triplets:[/bold]")
        for i, triplet in enumerate(graph_data.triplets, 1):
            self.display.print(
                f"[dim]{i:2d}. {triplet.subject} → {triplet.predicate} → {triplet.object}[/dim]"
            )

        remove_input = Prompt.ask(
            "\nEnter triplet numbers to remove (comma-separated, e.g., '1,3,5')",
            default="",
        )

        if remove_input.strip():
            try:
                # Parse the input
                indices_to_remove = [
                    int(x.strip()) - 1
                    for x in remove_input.split(",")
                    if x.strip().isdigit()
                ]
                indices_to_remove = [
                    i for i in indices_to_remove if 0 <= i < len(graph_data.triplets)
                ]

                if indices_to_remove:
                    # Remove triplets (in reverse order to maintain indices)
                    for i in sorted(indices_to_remove, reverse=True):
                        removed_triplet = graph_data.triplets.pop(i)
                        self.display.print(
                            f"[red]❌ Removed: {removed_triplet.subject} → {removed_triplet.predicate} → {removed_triplet.object}[/red]"
                        )

                    self.display.print(
                        f"[green]✅ Removed {len(indices_to_remove)} triplet(s)[/green]"
                    )
                else:
                    self.display.print(
                        "[yellow]No valid triplet numbers provided.[/yellow]"
                    )

            except ValueError:
                self.display.print(
                    "[red]❌ Invalid input format. Please use comma-separated numbers.[/red]"
                )
        else:
            self.display.print("[yellow]No triplets specified for removal.[/yellow]")

    def _show_detailed_triplet_view(self, graph_data):
        """Show detailed view of all triplets with descriptions"""
        self.display.print("\n[bold cyan]👀 Detailed Triplet View[/bold cyan]")

        if not graph_data.triplets:
            self.display.print("[yellow]No triplets to display.[/yellow]")
            return

        # Paginate through triplets
        page_size = 5
        total_triplets = len(graph_data.triplets)
        current_page = 0

        while True:
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, total_triplets)

            self.display.print(
                f"\n[bold]Triplets {start_idx + 1}-{end_idx} of {total_triplets}:[/bold]"
            )

            for i in range(start_idx, end_idx):
                triplet = graph_data.triplets[i]
                self.display.print(
                    f"\n[bold cyan]{i + 1}. {triplet.subject} → {triplet.predicate} → {triplet.object}[/bold cyan]"
                )
                self.display.print(
                    f"[dim]   Subject Type: {triplet.subject_type}[/dim]"
                )
                self.display.print(f"[dim]   Object Type: {triplet.object_type}[/dim]")
                if (
                    hasattr(triplet, "subject_description")
                    and triplet.subject_description
                ):
                    self.display.print(
                        f"[dim]   Subject: {triplet.subject_description}[/dim]"
                    )
                if (
                    hasattr(triplet, "object_description")
                    and triplet.object_description
                ):
                    self.display.print(
                        f"[dim]   Object: {triplet.object_description}[/dim]"
                    )
                if (
                    hasattr(triplet, "relationship_description")
                    and triplet.relationship_description
                ):
                    self.display.print(
                        f"[dim]   Relationship: {triplet.relationship_description}[/dim]"
                    )

            # Navigation options
            nav_options = []
            if current_page > 0:
                nav_options.append("p")
            if end_idx < total_triplets:
                nav_options.append("n")
            nav_options.append("b")

            nav_prompt = "Navigation: "
            if "p" in nav_options:
                nav_prompt += "[p]revious, "
            if "n" in nav_options:
                nav_prompt += "[n]ext, "
            nav_prompt += "[b]ack to review menu"

            choice = Prompt.ask(nav_prompt, choices=nav_options, default="b")

            if choice == "p":
                current_page -= 1
            elif choice == "n":
                current_page += 1
            elif choice == "b":
                break

    def display_ingested_resumes(self):
        """Display all ingested resumes from the database"""
        storage_service = ResumeStorageService()

        self.display.print("\n[bold cyan]📚 Ingested Resumes[/bold cyan]")
        self.display.print("[dim]All resumes stored in the database[/dim]\n")

        # Get all resumes
        all_resumes = storage_service.get_all_resumes()

        if not all_resumes:
            self.display.print("[yellow]No resumes found in the database.[/yellow]")
            self.display.print("[dim]Ingest a resume to see it here.[/dim]")
            return

        # Create summary table
        summary_table = Table(title="Resume Database Summary", show_header=True)
        summary_table.add_column("Status", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        total_count = len(all_resumes)
        completed_count = storage_service.get_resume_count("completed")
        pending_count = storage_service.get_resume_count("pending")
        failed_count = storage_service.get_resume_count("failed")

        summary_table.add_row("Total Resumes", str(total_count))
        summary_table.add_row("✅ Completed", str(completed_count))
        summary_table.add_row("⏳ Pending", str(pending_count))
        summary_table.add_row("❌ Failed", str(failed_count))

        self.display.console.print(summary_table)

        # Create detailed resumes table
        self.display.print("\n[bold]Resume Details:[/bold]")

        resumes_table = Table(show_header=True, header_style="bold magenta")
        resumes_table.add_column("ID", style="dim", width=12)
        resumes_table.add_column("File Name", style="cyan", width=30)
        resumes_table.add_column("Type", justify="center", width=8)
        resumes_table.add_column("Size", justify="right", width=10)
        resumes_table.add_column("Status", justify="center", width=12)
        resumes_table.add_column("Graph", justify="center", width=8)
        resumes_table.add_column("Created", width=20)

        for resume in all_resumes:
            # Format file size
            size_kb = resume.file_size / 1024
            size_str = f"{size_kb:.1f} KB"

            # Status emoji
            status_map = {
                "completed": "✅ Done",
                "pending": "⏳ Pending",
                "failed": "❌ Failed",
            }
            status_str = status_map.get(
                resume.ingestion_status, resume.ingestion_status
            )

            # Graph ingested
            graph_str = "✅" if resume.graph_ingested else "❌"

            # Format date
            try:
                created_dt = datetime.fromisoformat(resume.created_at)
                created_str = created_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                created_str = resume.created_at[:16] if resume.created_at else "N/A"

            resumes_table.add_row(
                resume.resume_id[:12],
                resume.file_name[:30],
                resume.file_type.upper(),
                size_str,
                status_str,
                graph_str,
                created_str,
            )

        self.display.console.print(resumes_table)

        # Show options
        self.display.print("\n[bold]Options:[/bold]")
        self.display.print("  1. View resume details")
        self.display.print("  2. Delete a resume")
        self.display.print("  3. Back to main menu")

        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3"], default="3")

        if choice == "1":
            self._view_resume_details(storage_service, all_resumes)
        elif choice == "2":
            self._delete_resume(storage_service, all_resumes)

    def _view_resume_details(self, storage_service, all_resumes):
        """View detailed information about a specific resume"""
        if not all_resumes:
            return

        self.display.print("\n[bold]Select a resume to view:[/bold]")
        for idx, resume in enumerate(all_resumes, 1):
            self.display.print(f"  {idx}. {resume.file_name} ({resume.resume_id[:12]})")

        choice = Prompt.ask("\nEnter resume number (or 'b' to go back)", default="b")

        if choice.lower() == "b":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_resumes):
                resume = all_resumes[idx]
                self._display_single_resume(resume)
            else:
                self.display.print("[red]Invalid selection.[/red]")
        except ValueError:
            self.display.print("[red]Invalid input.[/red]")

    def _display_single_resume(self, resume):
        """Display detailed information about a single resume"""
        self.display.print(
            f"\n[bold cyan]📄 Resume Details: {resume.file_name}[/bold cyan]"
        )
        self.display.print("=" * 60)

        details_table = Table(show_header=False, box=None)
        details_table.add_column("Field", style="bold cyan", width=20)
        details_table.add_column("Value", style="white")

        details_table.add_row("Resume ID", resume.resume_id)
        details_table.add_row("File Name", resume.file_name)
        details_table.add_row("File Path", resume.file_path)
        details_table.add_row("File Type", resume.file_type.upper())
        details_table.add_row("File Size", f"{resume.file_size / 1024:.1f} KB")
        details_table.add_row("Status", resume.ingestion_status)
        details_table.add_row(
            "Graph Ingested", "Yes" if resume.graph_ingested else "No"
        )
        details_table.add_row("Created At", resume.created_at)
        details_table.add_row("Updated At", resume.updated_at)
        if resume.ingested_at:
            details_table.add_row("Ingested At", resume.ingested_at)
        if resume.error_message:
            details_table.add_row("Error", resume.error_message)

        self.display.console.print(details_table)

        # Show content preview
        if resume.cleaned_content:
            self.display.print("\n[bold]Cleaned Content Preview:[/bold]")
            preview = resume.cleaned_content[:500]
            if len(resume.cleaned_content) > 500:
                preview += "..."
            self.display.print(f"[dim]{preview}[/dim]")

        Prompt.ask("\nPress Enter to continue", default="")

    def _delete_resume(self, storage_service, all_resumes):
        """Delete a resume from the database"""
        if not all_resumes:
            return

        self.display.print("\n[bold red]⚠️  Delete Resume[/bold red]")
        self.display.print(
            "[dim]This will only remove the database entry, not the original file.[/dim]\n"
        )

        for idx, resume in enumerate(all_resumes, 1):
            self.display.print(f"  {idx}. {resume.file_name} ({resume.resume_id[:12]})")

        choice = Prompt.ask(
            "\nEnter resume number to delete (or 'b' to go back)", default="b"
        )

        if choice.lower() == "b":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_resumes):
                resume = all_resumes[idx]

                if Confirm.ask(
                    f"\nAre you sure you want to delete '{resume.file_name}'?",
                    default=False,
                ):
                    if storage_service.delete_resume(resume.resume_id):
                        self.display.print(
                            "[green]✅ Resume deleted successfully.[/green]"
                        )
                    else:
                        self.display.print("[red]❌ Failed to delete resume.[/red]")
            else:
                self.display.print("[red]Invalid selection.[/red]")
        except ValueError:
            self.display.print("[red]Invalid input.[/red]")

    async def select_resume_for_optimization(self) -> Optional[str]:
        """
        Display list of completed resumes and let user select one for optimization.

        Returns:
            Resume ID if selected, None if cancelled
        """
        from ..persistence.resume_storage_service import ResumeStorageService

        storage_service = ResumeStorageService()
        all_resumes = storage_service.get_all_resumes()

        # Convert to dictionaries and filter to only completed resumes
        completed_resumes = [
            r.to_dict() for r in all_resumes if r.ingestion_status == "completed"
        ]

        if not completed_resumes:
            self.display.print(
                "\n[yellow]⚠️  No completed resumes found. Please ingest a resume first.[/yellow]"
            )
            Prompt.ask("\nPress Enter to continue", default="")
            return None

        self.display.print(
            "\n[bold cyan]✨ Resume Optimizer - Select Resume[/bold cyan]"
        )
        self.display.print("[dim]Choose a resume to analyze and optimize:[/dim]\n")

        # Display resumes in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("File Name", style="cyan")
        table.add_column("Ingested", style="green")
        table.add_column("Resume ID", style="dim")

        for idx, resume in enumerate(completed_resumes, 1):
            ingested_date = resume.get("ingested_at", "N/A")
            if ingested_date != "N/A":
                ingested_date = datetime.fromisoformat(ingested_date).strftime(
                    "%Y-%m-%d %H:%M"
                )

            table.add_row(
                str(idx),
                resume.get("file_name", "Unknown"),
                ingested_date,
                resume.get("resume_id", "")[:12] + "...",
            )

        self.display.console.print(table)

        choice = Prompt.ask("\nEnter resume number (or 'b' to go back)", default="b")

        if choice.lower() == "b":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(completed_resumes):
                return completed_resumes[idx].get("resume_id")
            else:
                self.display.print("[red]Invalid selection.[/red]")
                return None
        except ValueError:
            self.display.print("[red]Invalid input.[/red]")
            return None

    def get_optimization_context(self) -> Optional[str]:
        """
        Get additional context from user for optimization.

        Returns:
            Additional context string or None
        """
        self.display.print("\n[bold cyan]📝 Additional Context (Optional)[/bold cyan]")
        self.display.print(
            "[dim]Provide any additional context to help with optimization:[/dim]"
        )
        self.display.print("[dim]Examples:[/dim]")
        self.display.print(
            "[dim]  • Target role: Senior Software Engineer at FAANG[/dim]"
        )
        self.display.print("[dim]  • Industry: Machine Learning / AI[/dim]")
        self.display.print("[dim]  • Focus areas: Leadership, technical depth[/dim]")
        self.display.print("[dim]  • Career goals: Transition to management[/dim]\n")

        context = Prompt.ask(
            "Enter additional context (or press Enter to skip)", default=""
        )

        return context.strip() if context.strip() else None

    def display_optimization_results(self, optimization_output):
        """
        Display optimization results in a user-friendly format.

        Args:
            optimization_output: ResumeOptimizationOutput object
        """
        self.display.print("\n" + "=" * 80)
        self.display.print(
            "[bold cyan]✨ Resume Optimization Analysis Complete[/bold cyan]"
        )
        self.display.print("=" * 80 + "\n")

        # Overall Assessment
        self.display.print("[bold yellow]📊 Overall Assessment[/bold yellow]")
        self.display.print(f"{optimization_output.overall_assessment}\n")

        # Strengths
        if optimization_output.strengths:
            self.display.print("[bold green]💪 Key Strengths[/bold green]")
            for idx, strength in enumerate(optimization_output.strengths, 1):
                self.display.print(f"  {idx}. {strength}")
            self.display.print()

        # ATS Compatibility
        score = optimization_output.ats_score
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        self.display.print(
            f"[bold {score_color}]🎯 ATS Score: {score}/100[/bold {score_color}]\n"
        )

        # Optimization Suggestions by Priority
        if optimization_output.optimization_suggestions:
            self._display_optimization_suggestions(
                optimization_output.optimization_suggestions
            )

        # Missing Information
        if optimization_output.missing_information:
            self._display_missing_information(optimization_output.missing_information)

        # Top Actions
        if optimization_output.top_actions:
            self.display.print("[bold magenta]🚀 Top Actions[/bold magenta]")
            for idx, action in enumerate(optimization_output.top_actions, 1):
                self.display.print(f"  {idx}. {action}")
            self.display.print()

        self.display.print("=" * 80 + "\n")
        Prompt.ask("Press Enter to continue", default="")

    def _display_optimization_suggestions(self, suggestions):
        """Display optimization suggestions grouped by priority"""
        # Group by priority
        high_priority = [s for s in suggestions if s.priority == "HIGH"]
        medium_priority = [s for s in suggestions if s.priority == "MEDIUM"]
        low_priority = [s for s in suggestions if s.priority == "LOW"]

        if high_priority:
            self.display.print("[bold red]🔴 HIGH Priority Optimizations[/bold red]")
            for idx, suggestion in enumerate(high_priority, 1):
                self._display_single_suggestion(idx, suggestion)

        if medium_priority:
            self.display.print(
                "[bold yellow]🟡 MEDIUM Priority Optimizations[/bold yellow]"
            )
            for idx, suggestion in enumerate(medium_priority, 1):
                self._display_single_suggestion(idx, suggestion)

        if low_priority:
            self.display.print("[bold blue]🔵 LOW Priority Optimizations[/bold blue]")
            for idx, suggestion in enumerate(low_priority, 1):
                self._display_single_suggestion(idx, suggestion)

    def _display_single_suggestion(self, idx, suggestion):
        """Display a single optimization suggestion"""
        self.display.print(
            f"\n  {idx}. [{suggestion.category}] {suggestion.suggestion}"
        )
        self.display.print(f"     [dim]{suggestion.rationale}[/dim]\n")

    def _display_missing_information(self, missing_info):
        """Display missing information"""
        self.display.print("[bold orange]❓ Missing Information[/bold orange]\n")

        for idx, info in enumerate(missing_info, 1):
            self.display.print(f"  {idx}. [{info.category}] {info.what_missing}")
            self.display.print(f"     [dim]{info.why_important}[/dim]\n")

    async def ask_resume_question(self) -> Optional[Tuple[str, str]]:
        """
        Interactive Q&A for a specific resume.

        Returns:
            Tuple of (resume_id, question) or None if cancelled
        """
        # Select resume
        resume_id = await self.select_resume_for_optimization()
        if not resume_id:
            return None

        self.display.print(
            "\n[bold cyan]💬 Ask a Question About This Resume[/bold cyan]"
        )
        self.display.print("[dim]Examples:[/dim]")
        self.display.print("[dim]  • What are the key technical skills?[/dim]")
        self.display.print("[dim]  • What companies has this person worked at?[/dim]")
        self.display.print("[dim]  • Summarize the work experience[/dim]")
        self.display.print("[dim]  • What projects has this person worked on?[/dim]")
        self.display.print("[dim]  • What is the educational background?[/dim]\n")

        question = Prompt.ask("Enter your question (or 'b' to go back)", default="b")

        if question.lower() == "b" or not question.strip():
            return None

        return (resume_id, question.strip())

    def ask_general_question(self) -> Optional[str]:
        """
        Ask a question across all resumes.

        Returns:
            Question string or None if cancelled
        """
        self.display.print(
            "\n[bold cyan]💬 Ask a Question Across All Resumes[/bold cyan]"
        )
        self.display.print("[dim]Examples:[/dim]")
        self.display.print(
            "[dim]  • Who has experience with Python and machine learning?[/dim]"
        )
        self.display.print("[dim]  • Find candidates with cloud computing skills[/dim]")
        self.display.print("[dim]  • Who has worked at FAANG companies?[/dim]")
        self.display.print("[dim]  • List all candidates with PhD degrees[/dim]\n")

        question = Prompt.ask("Enter your question (or 'b' to go back)", default="b")

        if question.lower() == "b" or not question.strip():
            return None

        return question.strip()

    def display_qa_answer(
        self, question: str, answer: str, show_separator: bool = True
    ):
        """Display Q&A answer in a formatted way"""
        if show_separator:
            self.display.print("\n" + "=" * 80)
            self.display.print("[bold cyan]💬 Question & Answer[/bold cyan]")
            self.display.print("=" * 80 + "\n")

        self.display.print("[bold yellow]❓ Question:[/bold yellow]")
        self.display.print(f"{question}\n")

        self.display.print("[bold green]✅ Answer:[/bold green]")
        self.display.print(f"{answer}\n")

        if show_separator:
            self.display.print("=" * 80 + "\n")

    def ask_chat_question(self, chat_number: int = 1) -> Optional[str]:
        """
        Ask a question in chat mode.

        Args:
            chat_number: The current chat message number

        Returns:
            Question string or None if user wants to exit
        """
        self.display.print(f"\n[bold cyan]💬 Message #{chat_number}[/bold cyan]")
        self.display.print(
            "[dim]Type your question or 'exit' to end chat, 'clear' to clear history[/dim]"
        )

        question = Prompt.ask("You", default="")

        if not question.strip():
            return None

        return question.strip()

    def show_qa_menu(self) -> str:
        """Display Q&A submenu"""
        self.display.print("\n[bold cyan]💬 Resume Q&A[/bold cyan]")
        self.display.print("[dim]Choose how you'd like to ask questions:[/dim]\n")

        menu_options = {
            "1": "💬 Ask about a specific resume",
            "2": "🔍 Search across all resumes",
            "3": "⬅️  Back to main menu",
        }

        for key, value in menu_options.items():
            self.display.print(f"  {key}. {value}")

        choice = Prompt.ask(
            "\nSelect an option", choices=list(menu_options.keys()), default="1"
        )

        return choice
