# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project automates intelligence gathering from LinkedIn for rapid event and conference preparation. Built for tight deadlines where conventional research isn't feasible, it performs smart data extraction to quickly identify the most relevant people and organizations to engage with.

The codebase follows MVP principles - focused, to-the-point solutions for immediate business needs:

- **MCP Server** (`src/linkedin_mcp_server/`): Core server for AI-driven LinkedIn interaction
- **Batch Intelligence Scrapers**: Automated processing of speaker lists, attendee data, and target profiles
- **Smart Discovery**: DuckDuckGo integration to find LinkedIn profiles from minimal search data

## Development Commands

### Environment Setup
```bash
# Install dependencies and setup environment
uv sync
uv sync --group dev  # For development with pre-commit hooks

# Create .env file (template)
make init-env
```

### Running the Server
```bash
# Standard MCP server mode
uv run main.py

# Development/debugging with visible browser
uv run main.py --no-headless --debug --no-lazy-init

# Skip setup prompts (for automation)
uv run main.py --no-setup
```

### Testing and Quality
```bash
make test      # Run pytest tests
make lint      # Run ruff, mypy, and pre-commit checks
```

### Intelligence Operations
```bash
# Discover targets from search terms (events, organizations, roles)
make search INPUT=data/search_terms.csv OUTPUT=data/search_results.json

# Extract intelligence from discovered profiles
make scrape INPUT=data/profiles.csv
```

## Architecture

### Core Components

- **Server** (`src/linkedin_mcp_server/server.py`): Main MCP server setup and tool registration
- **Intelligence Tools** (`src/linkedin_mcp_server/tools/`):
  - `person.py`: Target profile extraction (`get_person_profile`)
  - `company.py`: Organization intelligence (`get_company_profile`)
  - `job.py`: Role and opportunity analysis (`get_job_details`)
  - `storage.py`: Intelligence storage and session management
- **Drivers** (`src/linkedin_mcp_server/drivers/chrome.py`): Chrome/Selenium WebDriver management
- **Config** (`src/linkedin_mcp_server/config/`): Configuration management system with secrets handling

### Operational Status
- **Production Ready**: Target profiling, organization analysis, role intelligence, session management
- **MVP Limitations**: Job search has ChromeDriver issues; recommended jobs needs method updates (low priority for current use cases)

### Intelligence Gathering Architecture
- `scraper.py`: Core batch processor for target identification and profile extraction
- `parse_ddg.py`: AI-powered parser for converting search results into actionable intelligence
- `groundswell_get_speakers.py`: Event-specific scraper for conference speaker intelligence

## Configuration

The server uses a centralized configuration system (`src/linkedin_mcp_server/config/`) that handles:
- LinkedIn credentials (stored securely in system keychain)
- Chrome browser settings and arguments
- Server transport modes (stdio/sse)
- Environment variable loading from `.env`

Required environment variables:
- `LINKEDIN_EMAIL`: LinkedIn login email
- `LINKEDIN_PASSWORD`: LinkedIn login password
- `CHROMEDRIVER`: Path to ChromeDriver (optional if in PATH)
- `ANTHROPIC_API_KEY`: Required for AI-powered intelligence parsing

## Dependencies

Key dependencies managed via `pyproject.toml`:
- `mcp[cli]`: Model Context Protocol framework
- `selenium`: Web automation for LinkedIn intelligence gathering
- `linkedin-scraper`: Custom fork optimized for profile extraction
- `anthropic`: AI processing for smart data extraction
- `pandas`: Data manipulation for intelligence processing

MVP stack: UV dependency management, Python 3.12+, minimal external dependencies for fast deployment.
