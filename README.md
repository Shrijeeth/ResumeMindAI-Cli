# ResumeMindAI CLI

AI-powered resume analysis and optimization tool with support for multiple LLM providers.

## Features

- **Multiple LLM Providers**: Support for GPT, Gemini, Claude, Ollama, and custom LiteLLM configurations
- **Interactive CLI**: Beautiful terminal interface with provider selection
- **Secure API Key Input**: Interactive prompts for API keys
- **LiteLLM Integration**: Unified interface for all providers

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

Run the CLI for an interactive provider selection:

```bash
python main.py
```

This will show you:

1. Available provider types (GPT, Gemini, Claude, Ollama, Custom)
2. Available models for each provider
3. Configuration validation
4. Selected configuration summary

## Supported Providers

### OpenAI GPT

- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Environment Variable**: `OPENAI_API_KEY`
- **LiteLLM Format**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Google Gemini

- **Models**: Gemini Pro, Gemini 1.5 Pro
- **Environment Variable**: `GOOGLE_API_KEY`
- **LiteLLM Format**: `gemini/gemini-pro`, `gemini/gemini-1.5-pro`

### Anthropic Claude

- **Models**: Claude 3 Opus, Sonnet, Haiku
- **Environment Variable**: `ANTHROPIC_API_KEY`
- **LiteLLM Format**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

### Ollama (Local)

- **Models**: Llama 2, Code Llama, Mistral
- **Base URL**: `http://localhost:11434` (default)
- **LiteLLM Format**: `ollama/llama2`, `ollama/codellama`, `ollama/mistral`

### Custom LiteLLM

- **Models**: Any model supported by LiteLLM
- **Configuration**: Custom model name, API key, and base URL

## API Keys

The CLI will prompt you to enter API keys when you select a provider that requires authentication. API keys are entered securely and are not stored.

## Example

```bash
python main.py
```

## Dependencies

- `litellm`: Unified LLM interface
- `rich`: Beautiful terminal output
- `agno`: Additional functionality
