"""
CLI interface for provider selection and configuration
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from rich.prompt import Confirm, Prompt
from rich.table import Table

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
            "2": "🤖 Manage Providers",
            "3": "❌ Exit",
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
