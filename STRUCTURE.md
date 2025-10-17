# Project Structure

This document describes the clean, modular structure of the ResumeMindAI CLI application.

## Directory Layout

```text
ResumeMindAI-Cli/
├── main.py                          # Clean entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
├── STRUCTURE.md                     # This file
├── resumemind/                      # Main package
│   ├── __init__.py                  # Package initialization
│   └── core/                        # Core functionality
│       ├── __init__.py              # Core module init
│       ├── providers/               # LLM provider management
│       │   ├── __init__.py          # Provider module exports
│       │   ├── base.py              # Base classes and enums
│       │   ├── config.py            # Provider configuration
│       │   └── registry.py          # Provider registry
│       ├── cli/                     # CLI interface components
│       │   ├── __init__.py          # CLI module exports
│       │   ├── interface.py         # User interaction logic
│       │   └── commands.py          # Command handlers
│       └── utils/                   # Utility functions
│           ├── __init__.py          # Utils module exports
│           └── display.py           # Rich display utilities
├── main_old.py                      # Backup of original main.py
└── providers_old.py                 # Backup of original providers.py
```

## Module Responsibilities

### `main.py`

- **Purpose**: Clean entry point for the application
- **Responsibilities**:
  - Initialize the main application class
  - Coordinate between CLI interface and command handlers
  - Handle application lifecycle

### `resumemind/core/providers/`

- **Purpose**: LLM provider management system
- **Components**:
  - `base.py`: Core enums and base classes
  - `config.py`: Provider configuration data structures
  - `registry.py`: Provider registry and management logic

### `resumemind/core/cli/`

- **Purpose**: Command-line interface components
- **Components**:
  - `interface.py`: User interaction and input handling
  - `commands.py`: Business logic and command processing

### `resumemind/core/utils/`

- **Purpose**: Shared utilities and helpers
- **Components**:
  - `display.py`: Rich terminal display management

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Clean Architecture**: Dependencies flow inward toward core business logic
3. **Modularity**: Components are loosely coupled and easily testable
4. **Extensibility**: New providers and commands can be added easily
5. **Maintainability**: Clear structure makes the codebase easy to understand and modify

## Benefits of This Structure

- **Testability**: Each component can be unit tested independently
- **Scalability**: Easy to add new features without affecting existing code
- **Readability**: Clear separation makes the codebase self-documenting
- **Reusability**: Components can be reused across different parts of the application
- **Maintainability**: Changes are localized to specific modules
