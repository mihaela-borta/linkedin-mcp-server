# Simple LinkedIn Message Generator

A streamlined LinkedIn outreach message generator that automatically loads CSV data, scrapes missing LinkedIn profiles, and generates personalized messages.

## What Changed

The original script was complex with:
- CSV loading and parsing
- LinkedIn profile slug handling
- Multiple data source management
- Complex scoring and filtering logic

This simplified version:
- **Loads CSV with LinkedIn URLs** (column name: `linkedin`)
- **Automatically scrapes missing profiles** using the LinkedIn MCP server
- **Extracts slugs from URLs** using existing logic from LinkedInScraper
- **Maintains the existing directory structure** (`~/linkedin_data/{event_name}/{slug}.json`)

## Required Input Format

Your CSV must have these columns (semicolon-separated):
- **name**: Speaker's full name
- **linkedin**: LinkedIn profile URL (required)
- **speaker_bio**: Brief speaker bio
- **detailed_profile**: Comprehensive profile information
- **selected_session**: Specific sessions they're involved in

**Note**: The event name is automatically inferred from the CSV filename (e.g., `groundswellag_speakers.csv` → event: `groundswellag`)

## Usage

### 1. Prepare Input Data

Create a CSV file with your speakers data:

```csv
name;linkedin;speaker_bio;detailed_profile;selected_session
Dr. Sarah Johnson;https://linkedin.com/in/sarah-johnson-12345;Leading researcher...;Dr. Johnson is a senior...;Advanced Soil Health...
Michael Chen;https://linkedin.com/in/michael-chen-agritech;Agricultural technology...;Michael Chen is the founder...;AI in Agriculture...
```

**Important**: Name your CSV file with the event prefix (e.g., `groundswellag_speakers.csv`, `agritech2024_attendees.csv`)

### 2. Run the Generator

```bash
python simple_message_generator.py --input speakers.csv --output messages.csv
```

### 3. Optional Parameters

- `--profiles`: Base directory for LinkedIn profiles (default: `$HOME/linkedin_data/`)
- `--output`: Output CSV file (default: `data/groundswell_outreach_messages.csv`)
- `--jsonl`: Intermediate JSONL file (default: `data/groundswell_outreach_messages.jsonl`)
- `--poll-interval`: Polling interval in seconds (default: 60)

## Example

```bash
# Generate messages for speakers in speakers.csv
python simple_message_generator.py --input speakers.csv

# Custom output location
python simple_message_generator.py --input speakers.csv --output my_messages.csv

# Custom profiles directory
python simple_message_generator.py --input speakers.csv --profiles ~/my_linkedin_data/
```

## How It Works

1. **Loads CSV data** with LinkedIn URLs
2. **Extracts slugs** from LinkedIn URLs using `linkedin_slug()` method
3. **Checks existing profiles** in `~/linkedin_data/{event_name}/{slug}.json`
4. **Automatically scrapes missing profiles** using the LinkedIn MCP server
5. **Generates personalized messages** using all available data

## Required Environment Variables

For LinkedIn profile scraping, you need:
- `LINKEDIN_EMAIL`: Your LinkedIn email
- `LINKEDIN_PASSWORD`: Your LinkedIn password  
- `CHROMEDRIVER`: Path to ChromeDriver executable

## Output

The script generates:
1. A JSONL file with Claude's raw responses
2. A CSV file with structured message data including:
   - Name
   - Generated message
   - Personalization source
   - Confidence level
   - Send recommendation

## Dependencies

- `anthropic` Python package
- `mcp_use` for LinkedIn MCP client
- `ANTHROPIC_API_KEY` environment variable
- The `utils` module from your existing codebase
- LinkedIn credentials and ChromeDriver for profile scraping

## Benefits of This Approach

1. **Fully automated**: No manual profile management needed
2. **Smart caching**: Only scrapes profiles that don't exist
3. **Rich personalization**: Combines speaker data + LinkedIn data for better messages
4. **Maintains structure**: Uses the same directory structure as your existing scraper
5. **Error handling**: Gracefully handles scraping failures and continues processing
6. **Resume capability**: Can resume from where it left off if interrupted

## When LinkedIn Scraping Happens

- **Immediate**: When a profile is missing
- **Automatic**: No user intervention required
- **Smart**: Only scrapes what's needed
- **Cached**: Results are saved for future use
