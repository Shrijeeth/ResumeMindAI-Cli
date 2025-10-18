"""
Provider management interface for handling multiple providers
"""

from typing import List, Optional, Tuple

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from ..persistence import ProviderStateService
from ..utils import DisplayManager
from .config import ProviderConfig
from .registry import LLMProviders


class ProviderManager:
    """Manages multiple LLM providers with persistence"""

    def __init__(self):
        self.state_service = ProviderStateService()
        self.display = DisplayManager()
        self.console = Console()

    def get_or_create_provider(self) -> Optional[Tuple[ProviderConfig, dict]]:
        """
        Get an existing provider or create a new one

        Returns:
            Tuple of (ProviderConfig, litellm_config) or None if cancelled
        """
        # Check if we have any saved providers
        if not self.state_service.has_providers():
            self.display.print(
                "\n[yellow]No saved providers found. Let's create your first provider![/yellow]"
            )
            return self._create_new_provider()

        # Show provider selection menu
        return self._show_provider_menu()

    def _show_provider_menu(self) -> Optional[Tuple[ProviderConfig, dict]]:
        """Show the main provider management menu"""
        while True:
            self.display.print("\n[bold cyan]🤖 Provider Management[/bold cyan]")

            # Get all providers
            providers = self.state_service.get_all_providers()
            active_provider = self.state_service.get_active_provider()

            if providers:
                self._display_providers_table(providers, active_provider)

            # Show menu options
            self.display.print("\n[bold]Available Actions:[/bold]")
            self.display.print("  1. 🚀 Use existing provider")
            self.display.print("  2. ➕ Add new provider")
            self.display.print("  3. ⚙️  Manage providers")
            self.display.print("  4. ❌ Exit")

            choice = Prompt.ask(
                "\nSelect an option",
                choices=["1", "2", "3", "4"],
                default="1" if providers else "2",
            )

            if choice == "1":
                if not providers:
                    self.display.print(
                        "[yellow]No providers available. Please add a provider first.[/yellow]"
                    )
                    continue
                return self._select_existing_provider(providers)

            elif choice == "2":
                result = self._create_new_provider()
                if result:
                    return result

            elif choice == "3":
                if not providers:
                    self.display.print(
                        "[yellow]No providers to manage. Please add a provider first.[/yellow]"
                    )
                    continue
                self._manage_providers(providers)

            elif choice == "4":
                return None

    def _display_providers_table(self, providers: List, active_provider: Optional):
        """Display providers in a formatted table"""
        table = Table(
            title="Saved Providers", show_header=True, header_style="bold magenta"
        )
        table.add_column("ID", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Last Updated", style="dim")

        for provider in providers:
            status_icons = []
            if provider.is_active or (
                active_provider and provider.id == active_provider.id
            ):
                status_icons.append("🟢 Active")
            if provider.is_default:
                status_icons.append("⭐ Default")

            status = " ".join(status_icons) if status_icons else "⚪ Inactive"

            # Format last updated
            if provider.updated_at:
                from datetime import datetime

                try:
                    updated = datetime.fromisoformat(provider.updated_at)
                    updated_str = updated.strftime("%m/%d %H:%M")
                except Exception:
                    updated_str = "Unknown"
            else:
                updated_str = "Unknown"

            table.add_row(
                str(provider.id),
                provider.name,
                provider.model,
                provider.provider_type.upper(),
                status,
                updated_str,
            )

        self.console.print(table)

    def _select_existing_provider(
        self, providers: List
    ) -> Optional[Tuple[ProviderConfig, dict]]:
        """Select an existing provider to use"""
        # Check if there's an active provider
        active_provider = self.state_service.get_active_provider()
        if active_provider:
            use_active = Confirm.ask(
                f"\nUse currently active provider '{active_provider.name}'?",
                default=True,
            )
            if use_active:
                result = self.state_service.get_provider_config_and_litellm(
                    active_provider.id
                )
                if result:
                    return result

        # Let user select a provider
        self.display.print("\n[bold]Select a provider to use:[/bold]")

        while True:
            try:
                provider_id = IntPrompt.ask(
                    "Enter provider ID", choices=[str(p.id) for p in providers if p.id]
                )

                # Set as active and get config
                if self.state_service.set_active_provider(provider_id):
                    result = self.state_service.get_provider_config_and_litellm(
                        provider_id
                    )
                    if result:
                        provider_name = next(
                            p.name for p in providers if p.id == provider_id
                        )
                        self.display.print(
                            f"[green]✅ Activated provider: {provider_name}[/green]"
                        )
                        return result

                self.display.print(
                    "[red]Failed to activate provider. Please try again.[/red]"
                )

            except (ValueError, KeyboardInterrupt):
                if not Confirm.ask("Would you like to try again?", default=True):
                    return None

    def _create_new_provider(self) -> Optional[Tuple[ProviderConfig, dict]]:
        """Create a new provider configuration"""
        self.display.print("\n[bold cyan]➕ Add New Provider[/bold cyan]")

        # Get configuration from user
        config, litellm_config = self._get_custom_model_config()
        if not config:
            return None

        # Ask if this should be the default
        is_default = False
        if not self.state_service.has_providers():
            is_default = True
            self.display.print("[dim]This will be set as your default provider.[/dim]")
        else:
            is_default = Confirm.ask("Set as default provider?", default=False)

        # Save the provider
        try:
            provider_id = self.state_service.save_provider(
                config,
                is_active=True,  # New providers are automatically active
                is_default=is_default,
            )

            self.display.print(
                f"[green]✅ Provider '{config.name}' saved successfully![/green]"
            )
            self.display.print(f"[dim]Provider ID: {provider_id}[/dim]")

            return config, litellm_config

        except Exception as e:
            self.display.print(f"[red]Failed to save provider: {str(e)}[/red]")
            return None

    def _get_custom_model_config(
        self,
    ) -> Tuple[Optional[ProviderConfig], Optional[dict]]:
        """Get custom model configuration from user"""
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

        try:
            # Get provider name
            provider_name = Prompt.ask(
                "Enter a name for this provider (e.g., 'My GPT-4')"
            )
            if not provider_name.strip():
                self.display.print("[red]Provider name cannot be empty.[/red]")
                return None, None

            # Check if name already exists
            existing = self.state_service.get_provider_by_name(provider_name)
            if existing:
                overwrite = Confirm.ask(
                    f"Provider '{provider_name}' already exists. Overwrite?",
                    default=False,
                )
                if not overwrite:
                    return None, None

            model = Prompt.ask("Enter model name")
            if not model.strip():
                self.display.print("[red]Model name cannot be empty.[/red]")
                return None, None

            api_key = Prompt.ask(
                "Enter API key (optional for local models like Ollama)",
                default="",
                password=True,
            )

            base_url = Prompt.ask(
                "Enter base URL (optional, e.g., http://localhost:11434 for Ollama)",
                default="",
            )

            # Create config with the custom name
            config, litellm_config = LLMProviders.create_custom_config(
                model=model,
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
            )

            # Update the config name to use the user-provided name
            config.name = provider_name

            return config, litellm_config

        except KeyboardInterrupt:
            self.display.print("\n[yellow]Provider creation cancelled.[/yellow]")
            return None, None

    def _manage_providers(self, providers: List):
        """Manage existing providers"""
        while True:
            self.display.print("\n[bold cyan]⚙️  Provider Management[/bold cyan]")
            self._display_providers_table(
                providers, self.state_service.get_active_provider()
            )

            self.display.print("\n[bold]Management Actions:[/bold]")
            self.display.print("  1. 🎯 Set active provider")
            self.display.print("  2. ⭐ Set default provider")
            self.display.print("  3. 🗑️  Delete provider")
            self.display.print("  4. 🔄 Refresh list")
            self.display.print("  5. ⬅️  Back to main menu")

            choice = Prompt.ask(
                "Select an action", choices=["1", "2", "3", "4", "5"], default="5"
            )

            if choice == "1":
                self._set_active_provider(providers)
            elif choice == "2":
                self._set_default_provider(providers)
            elif choice == "3":
                providers = self._delete_provider(providers)
                if not providers:  # If no providers left, return to main menu
                    break
            elif choice == "4":
                providers = self.state_service.get_all_providers()
            elif choice == "5":
                break

    def _set_active_provider(self, providers: List):
        """Set a provider as active"""
        try:
            provider_id = IntPrompt.ask(
                "Enter provider ID to set as active",
                choices=[str(p.id) for p in providers if p.id],
            )

            if self.state_service.set_active_provider(provider_id):
                provider_name = next(p.name for p in providers if p.id == provider_id)
                self.display.print(
                    f"[green]✅ Set '{provider_name}' as active provider[/green]"
                )
            else:
                self.display.print("[red]Failed to set active provider[/red]")

        except (ValueError, KeyboardInterrupt):
            self.display.print("[yellow]Action cancelled[/yellow]")

    def _set_default_provider(self, providers: List):
        """Set a provider as default"""
        try:
            provider_id = IntPrompt.ask(
                "Enter provider ID to set as default",
                choices=[str(p.id) for p in providers if p.id],
            )

            if self.state_service.set_default_provider(provider_id):
                provider_name = next(p.name for p in providers if p.id == provider_id)
                self.display.print(
                    f"[green]✅ Set '{provider_name}' as default provider[/green]"
                )
            else:
                self.display.print("[red]Failed to set default provider[/red]")

        except (ValueError, KeyboardInterrupt):
            self.display.print("[yellow]Action cancelled[/yellow]")

    def _delete_provider(self, providers: List) -> List:
        """Delete a provider"""
        try:
            provider_id = IntPrompt.ask(
                "Enter provider ID to delete",
                choices=[str(p.id) for p in providers if p.id],
            )

            provider_to_delete = next(p for p in providers if p.id == provider_id)

            # Confirm deletion
            if not Confirm.ask(
                f"Are you sure you want to delete '{provider_to_delete.name}'?",
                default=False,
            ):
                self.display.print("[yellow]Deletion cancelled[/yellow]")
                return providers

            if self.state_service.delete_provider(provider_id):
                self.display.print(
                    f"[green]✅ Deleted provider '{provider_to_delete.name}'[/green]"
                )
                # Return updated list
                return self.state_service.get_all_providers()
            else:
                self.display.print("[red]Failed to delete provider[/red]")
                return providers

        except (ValueError, KeyboardInterrupt):
            self.display.print("[yellow]Action cancelled[/yellow]")
            return providers
