# LinkedIn MCP Server

[![smithery badge](https://smithery.ai/badge/@stickerdaniel/linkedin-mcp-server)](https://smithery.ai/server/@stickerdaniel/linkedin-mcp-server)

A Model Context Protocol (MCP) server that enables interaction with LinkedIn through Claude and other AI assistants. This server allows you to scrape LinkedIn profiles, companies, jobs, and perform job searches.

## Features & Tool Status

### Working Tools

* **Profile Scraping** (`get_person_profile`): Get detailed information from LinkedIn profiles including work history, education, skills, and connections
* **Company Analysis** (`get_company_profile`): Extract company information with comprehensive details
* **Job Details** (`get_job_details`): Retrieve specific job posting details using direct LinkedIn job URLs
* **Session Management** (`close_session`): Properly close browser sessions and clean up resources
* **Batch Profile Scraping**: Use the included scraper to process multiple profiles from a CSV file

### Tools with Known Issues

* **Job Search** (`search_jobs`): Currently experiencing ChromeDriver compatibility issues with LinkedIn's search interface
* **Recommended Jobs** (`get_recommended_jobs`): Has Selenium method compatibility issues due to outdated scraping methods
* **Company Profiles**: Some companies may have restricted access or may return empty results (need further investigation)

## Installation

### Prerequisites

* Python 3.12 or higher
* Chrome browser installed
* ChromeDriver matching your Chrome version (we'll help you set this up)
* A LinkedIn account

### Quick Start (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/linkedin-mcp-server
cd linkedin-mcp-server

# 2. Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install the project and all dependencies
uv sync

# 4. Create a .env file with your credentials
cp .env.example .env
# Edit .env with your LinkedIn credentials:
# - LINKEDIN_EMAIL: Your LinkedIn email
# - LINKEDIN_PASSWORD: Your LinkedIn password
# - CHROMEDRIVER: (Optional) Path to ChromeDriver if not in PATH
# - SCRAPER_DELAY: (Optional) Delay between requests in seconds (default: 180)
```

#### For Development

If you want to contribute or modify the code:

```bash
# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

### ChromeDriver Setup

ChromeDriver is required for Selenium to interact with Chrome. You need to install the version that matches your Chrome browser.

1. **Check your Chrome version**:
   * Open Chrome and go to the menu (three dots) > Help > About Google Chrome
   * Note the version number (e.g., 123.0.6312.87)
2. **Download matching ChromeDriver**:
   * Go to ChromeDriver Downloads / Chrome for Testing (Chrome-Version 115+)
   * Download the version that matches your Chrome version
   * Extract the downloaded file
3. **Make ChromeDriver accessible**:
   * **Option 1**: Place it in a directory that's in your PATH (e.g., `/usr/local/bin` on macOS/Linux)
   * **Option 2**: Set the CHROMEDRIVER environment variable to the path where you placed it:
     ```bash
     export CHROMEDRIVER=/path/to/chromedriver  # macOS/Linux
     # OR
     set CHROMEDRIVER=C:\path\to\chromedriver.exe  # Windows
     ```
   * **Option 3**: The server will attempt to auto-detect or prompt you for the path when run

## Running the Server

### Quick Start

After installation, run:

```bash
# Start the server (first time setup)
uv run main.py --no-lazy-init --no-headless
```

### Running Options

```bash
# Normal operation (lazy initialization)
uv run main.py

# Debug mode with visible browser and direct startup
uv run main.py --no-headless --debug --no-lazy-init

# Skip setup prompts (for automation)
uv run main.py --no-setup
```

### Batch Profile Scraping

The included scraper allows you to process multiple LinkedIn profiles from a CSV file:

1. Create a CSV file in `data/profiles.csv` with columns:
   - `name`: Profile name (for logging)
   - `url`: LinkedIn profile URL

2. Run the scraper:
```bash
uv run scraper.py
```

The scraper will:
- Process each profile in the CSV
- Wait between requests to avoid rate limiting
- Log results and any errors
- Save profile data as needed

You can adjust the delay between requests by modifying the `delay_seconds` parameter in `scraper.py`.

### Configuration for Claude Desktop

1. **The server will automatically**:
   * Display the configuration needed for Claude Desktop
   * Copy it to your clipboard for easy pasting
2. **Add to Claude Desktop**:
   * Open Claude Desktop and go to Settings > Developer > Edit Config
   * Paste the configuration provided by the server

Example Claude Desktop configuration:
```json
{
  "mcpServers": {
    "linkedin-scraper": {
      "command": "uv",
      "args": ["--directory", "/path/to/linkedin-mcp-server", "run", "main.py", "--no-setup"],
      "env": {
        "LINKEDIN_EMAIL": "your.email@example.com",
        "LINKEDIN_PASSWORD": "your_password"
      }
    }
  }
}
```

## Security and Privacy

* Your LinkedIn credentials are stored securely in your system's native keychain/credential manager with user-only permissions
* Credentials are never exposed to Claude or any other AI and are only used for the LinkedIn login to scrape data
* The server runs on your local machine, not in the cloud
* All LinkedIn scraping happens through your account - be aware that profile visits are visible to other users

## Troubleshooting

### ChromeDriver Issues

If you encounter ChromeDriver errors:

1. Ensure your Chrome browser is updated
2. Download the matching ChromeDriver version
3. Set the CHROMEDRIVER path correctly
4. Try running with administrator/sudo privileges if permission issues occur

### Authentication Issues

If login fails:

1. Verify your LinkedIn credentials
2. Check if your account has two-factor authentication enabled
3. Try logging in manually to LinkedIn first, then run the server
4. Check your LinkedIn mobile app for a login request after running the server
5. Try to run the server with `--no-headless` to see where the login fails
6. Try to run the server with `--debug` to see more detailed logs

## License

This project is licensed under the MIT License

## Acknowledgements

* Based on the LinkedIn Scraper by joeyism
* Uses the Model Context Protocol (MCP) for integration with AI assistants

---

**Note**: This tool is for personal use only. Use responsibly and in accordance with LinkedIn's terms of service. Web scraping may violate LinkedIn's terms of service.
