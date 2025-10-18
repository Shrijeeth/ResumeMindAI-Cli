"""
CLI interface for provider selection and configuration
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from rich.prompt import Confirm, Prompt

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
