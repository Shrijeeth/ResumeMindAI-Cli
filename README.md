# ResumeMindAI CLI

AI-powered resume analysis tool built for IT professionals, freelancers, and consultants. Transform your resume into structured knowledge graphs using GraphRAG technology with multi-provider LLM support.

## What It Does

ResumeMindAI CLI converts your resume into a **structured knowledge graph** that captures entities (skills, companies, projects) and their semantic relationships. This enables intelligent analysis and optimization of your professional profile.

## Core Features

### 📄 Resume Processing Pipeline

- **Document Parsing**: Supports PDF, DOCX, DOC, and TXT files
- **AI-Powered Cleaning**: Standardizes and formats resume content
- **Section-Based Analysis**: Processes education, experience, skills, projects separately for better accuracy
- **Human-in-the-Loop**: Interactive review system to validate and refine extracted data

### 🧠 GraphRAG & Vector Embeddings

- **Knowledge Graph Creation**: Converts resumes into structured graph databases with FalkorDB
- **Semantic Relationships**: Captures connections between skills, experiences, and achievements
- **Vector Embeddings**: Multi-provider support (OpenAI, Ollama, Google) for semantic search
- **Intelligent Querying**: Search and analyze your professional data semantically

### 🤖 Multi-Provider LLM Support

- **Universal Compatibility**: Works with OpenAI, Anthropic, Google Gemini, Ollama, and 100+ models via LiteLLM
- **Persistent Configuration**: Save multiple provider setups and switch between them seamlessly
- **Smart Startup**: Automatically loads your active provider on startup
- **Local & Cloud**: Mix cloud LLMs with local embeddings for cost optimization
- **Privacy First**: Complete offline operation possible with Ollama
- **Rich CLI Interface**: Beautiful terminal UI with interactive menus and tables

### 🎯 Built For Professionals

- **IT Professionals**: Analyze technical skills, project portfolios, and career progression
- **Freelancers**: Understand expertise positioning and identify skill gaps
- **Consultants**: Optimize professional profiles for client presentations
- **Job Seekers**: Prepare for interviews with structured skill analysis
- **Career Development**: Make data-driven decisions about your professional growth

## Quick Start

### Prerequisites

- Python 3.8+
- Docker (for FalkorDB graph database)

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd ResumeMindAI-Cli
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Start the graph database:**

```bash
docker-compose up -d
```

This starts FalkorDB with web interface accessible at `http://localhost:3010`

4. **Run the application:**

```bash
python main.py
```

## How It Works

### The Resume → Graph Pipeline

1. **📄 Upload Resume**: Supports PDF, DOCX, DOC, TXT formats
2. **🧹 AI Cleaning**: Standardizes and formats content using LLM
3. **📊 Section Parsing**: Automatically detects education, experience, skills, projects
4. **🧠 Graph Extraction**: AI agents extract entities and relationships
5. **👤 Human Review**: Interactive validation and refinement of extracted data
6. **🔢 Vector Embeddings**: Generate semantic embeddings for search
7. **💾 Graph Storage**: Store in FalkorDB for querying and analysis

### First Time Setup

On your first run, you'll configure an LLM provider:

- **Provider Name**: Custom name (e.g., "My GPT-4", "Local Ollama")
- **Model**: Any LiteLLM-supported model (`gpt-4o`, `claude-3-5-sonnet-20241022`, `ollama/llama3.2`)
- **API Key**: Required for cloud providers, optional for local models
- **Base URL**: Optional (e.g., `http://localhost:11434` for Ollama)
- **Embedding Model**: Auto-selected or custom (e.g., `text-embedding-3-small`, `ollama/nomic-embed-text`)

### Main Menu Options

After setup, you'll see the main menu:

```text
🎯 ResumeMindAI - Main Menu
1. 📄 Resume Ingestion - Process and analyze your resume
2. 🤖 Manage Providers - Add, switch, or configure LLM providers
3. ❌ Exit
```

### Resume Ingestion Process

1. **Select Resume File**: Choose your PDF, DOCX, or TXT resume
2. **AI Processing**: Watch as the system processes each section
3. **Review Extracted Data**: Validate triplets (relationships) found in your resume
4. **Refine Results**: Add missing information or remove incorrect data
5. **Graph Storage**: Approve final results for storage in the knowledge graph
6. **🌐 View Graph**: Access FalkorDB web interface at `http://localhost:3010` to explore your resume graph visually

The human-in-the-loop review ensures accuracy - you have full control over what gets stored.

### 🔍 Exploring Your Resume Graph

After processing your resume, you can visualize and query your knowledge graph:

- **Web Interface**: Open `http://localhost:3010` in your browser
- **Visual Exploration**: See entities (skills, companies, projects) and their relationships
- **Graph Queries**: Run Cypher queries to analyze your professional data
- **Interactive Navigation**: Click through connected nodes to explore relationships

## Tech Stack & Architecture

### Core Technologies

- **Python**: Main application language
- **LiteLLM**: Unified interface for 100+ LLM providers
- **FalkorDB**: Graph database for storing resume relationships
- **Rich**: Beautiful terminal UI with tables and interactive prompts
- **Agno**: AI agent framework for resume processing workflows
- **MarkItDown**: Document parsing for PDF, DOCX, and other formats
- **SQLite**: Local persistence for provider configurations

### Supported LLM Providers

**Cloud Providers:**

- OpenAI: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- Google: `gemini/gemini-1.5-pro`, `gemini/gemini-pro`
- Azure OpenAI, Cohere, Perplexity, Together AI, and 100+ more

**Local Models (Ollama):**

- `ollama/llama3.2`, `ollama/llama3.1`, `ollama/mistral`, `ollama/codellama`

### Architecture Benefits

- **Privacy First**: All data stored locally, no external dependencies except LLM APIs
- **Modular Design**: Clean separation between CLI, agents, services, and persistence
- **Extensible**: Easy to add new agents and processing workflows
- **Cost Flexible**: Mix expensive cloud LLMs with free local embeddings

## Future Roadmap

### Planned AI Agents

The current v1 focuses on resume → graph conversion. Future versions will add specialized agents:

- **🎯 Interview Prep Agent**: Generate technical questions based on your extracted skills and experience
- **📊 Skills Gap Analyzer**: Compare your profile against job requirements and market trends
- **💼 Portfolio Optimizer**: Suggest improvements to your projects and achievements
- **🚀 Career Path Predictor**: Recommend next career moves based on your background
- **📈 Market Position Analyzer**: Compare your profile against industry standards
- **📝 Resume Optimizer**: Suggest improvements to resume content and structure

### Web Interface (Coming Soon)

While v1 is CLI-focused, a web interface is planned for future releases with:

- Visual graph exploration
- Interactive resume editing
- Dashboard analytics
- Collaborative features

### Contributing

We welcome contributions! The modular architecture makes it easy to add new agents and features. Check the `resumemind/core/agents/` directory for examples.

## Data Privacy & Security

- **Local Storage**: All resume data and configurations stored locally
- **No Data Collection**: No telemetry or data sent to external services
- **API Key Security**: Credentials stored securely in local SQLite database
- **Open Source**: Full transparency - audit the code yourself

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### Apache License 2.0

ResumeMindAI CLI is free and open-source software that allows you to:

- ✅ **Use** the software for any purpose
- ✅ **Modify** the source code
- ✅ **Distribute** copies of the software
- ✅ **Distribute** modified versions
- ✅ **Use** for commercial purposes

**Requirements:**

- Include the original copyright notice and license
- State any significant changes made to the software

**No Warranty:** The software is provided "as is" without warranty of any kind.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join the community for questions and ideas
- **Documentation**: Full API docs available in the codebase

---

**Built for developers, by developers. Transform your resume analysis workflow with AI-powered insights.**
