# ResumeMindAI CLI

AI-powered resume analysis and optimization tool with persistent provider management and support for multiple LLM providers.

## Features

- **🔄 Persistent Provider Management**: Save, manage, and switch between multiple LLM providers
- **🚀 Smart Startup**: Automatically loads your active provider on startup
- **🎨 Rich Interactive UI**: Beautiful terminal interface with provider tables and management menus
- **🤖 Agent-Ready**: Clean API for programmatic provider management
- **🔧 Universal LLM Support**: Any model supported by LiteLLM (OpenAI, Anthropic, Google, Ollama, etc.)
- **💾 SQLite Persistence**: Providers persist across application restarts
- **🔒 Secure Storage**: API keys and configurations stored locally

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd ResumeMindAI-Cli
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### First Run

When you run the application for the first time:

```bash
python main.py
```

You'll be prompted to create your first provider:

1. Enter a custom name for your provider (e.g., "My GPT-4")
2. Specify the model (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`)
3. Enter API key (if required)
4. Set base URL (if needed, e.g., for Ollama)

### Subsequent Runs

The application will automatically load your active provider and start the main menu:

```text
🎯 ResumeMindAI - Main Menu
1. 📄 Resume Ingestion
2. 🤖 Manage Providers  
3. ❌ Exit
```

### Provider Management

Select "🤖 Manage Providers" to:

- ➕ **Add new providers**: Create additional provider configurations
- 🎯 **Set active provider**: Switch which provider is currently active
- ⭐ **Set default provider**: Choose your preferred fallback provider
- 🗑️ **Delete providers**: Remove unused provider configurations
- 📋 **View all providers**: See all saved providers with status indicators

## Supported Providers

ResumeMindAI CLI supports **any model compatible with LiteLLM**. Here are some popular examples:

### OpenAI Models

```text
gpt-4o
gpt-4
gpt-4-turbo
gpt-3.5-turbo
```

### Anthropic Claude Models

```text
claude-3-5-sonnet-20241022
claude-3-opus-20240229
claude-3-sonnet-20240229
claude-3-haiku-20240307
```

### Google Gemini Models

```text
gemini/gemini-1.5-pro
gemini/gemini-pro
gemini/gemini-1.5-flash
```

### Ollama (Local Models)

```text
ollama/llama3.2
ollama/llama3.1
ollama/mistral
ollama/codellama
ollama/qwen2.5
```

### Other Providers

- **Azure OpenAI**: `azure/gpt-4`
- **Cohere**: `cohere/command-r-plus`
- **Perplexity**: `perplexity/llama-3.1-sonar-large-128k-online`
- **Together AI**: `together_ai/meta-llama/Llama-2-70b-chat-hf`
- **And many more**: Any provider supported by LiteLLM

## Data Storage

### Provider Persistence

- **Database Location**: `~/.resumemind/providers.db` (SQLite)
- **Stored Data**: Provider configurations, model names, API keys, base URLs
- **Security**: All data stored locally on your machine

### API Keys

- API keys are stored securely in the local SQLite database
- Keys are only accessible from your local machine
- No data is sent to external services except for LLM API calls

## Architecture

### Core Components

- **`resumemind/core/persistence/`**: SQLite-based persistence layer
  - `models.py`: Database models and data conversion utilities
  - `service.py`: Thread-safe singleton service for database operations
- **`resumemind/core/providers/`**: Provider management system
  - `manager.py`: Rich UI for interactive provider management
  - `registry.py`: LiteLLM configuration utilities
  - `config.py`: Provider configuration data classes
- **`resumemind/core/cli/`**: Command-line interface
  - `interface.py`: User interaction and input validation
  - `commands.py`: Business logic and workflow orchestration

### Agent Integration

For programmatic access, use the `ProviderStateService`:

```python
from resumemind.core.persistence import ProviderStateService

# Initialize service
service = ProviderStateService()

# Save a provider
provider_id = service.save_provider(config, is_active=True)

# Get active provider
active_provider = service.get_active_provider()

# Get provider config for LiteLLM
config, litellm_config = service.get_provider_config_and_litellm(provider_id)
```

## Dependencies

- **`litellm`**: Unified LLM interface supporting 100+ models
- **`rich`**: Beautiful terminal UI with tables and interactive prompts
- **`agno`**: AI agent framework for resume processing workflows
- **`falkordb`**: Graph database for resume data storage
- **`markitdown`**: Document parsing for PDF, DOCX, and other formats
