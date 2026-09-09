# groundswellag Festival Data Scripts

## Script: 0_groundswellag_get_speakers_from_website.py

**Purpose:**
Extracts speaker names and their session URLs from the festival website and saves them as a CSV file.

**Input:**
- Website URL (default: https://groundswellag.com/2025-speakers/)

**Output:**
- CSV file with columns: `name`, `session` (default: data/groundswellag_speaker_webpages.csv)

**Example usage:**
```bash
uv run 0_groundswellag_get_speakers_from_website.py \
    --url https://groundswellag.com/2025-speakers/ \
    --output data/groundswellag_speaker_webpages.csv
```

---

## Script: 1_groundswellag_get_speaker_details_from_speaker_page.py

**Purpose:**
Scrapes detailed speaker bios and session information from each speaker's page using the Firecrawl API.

**Input:**
- CSV file with columns: `name`, `url` or `speaker_page` (default: data/groundswellag_speaker_webpages.csv)

**Output:**
- CSV file with detailed speaker bios and up to 3 sessions per speaker (default: data/groundswellag_speakers.csv)

**Example usage:**
```bash
uv run 1_groundswellag_get_speaker_details_from_speaker_page.py \
    --input data/groundswellag_speaker_webpages.csv \
    --output data/groundswellag_speakers.csv \
    --batch-size 10
```

---

## Script: 2_groundswellag_enhance_speaker_with_sessions.py

**Purpose:**
Combines handpicked and all session data for Groundswell speakers, aggregates sessions per speaker, and joins with speaker bios using fuzzy name matching.

**Input:**
- CSV with all sessions (default: data/groundswellag_sessions_clean.csv)
- CSV with handpicked sessions (default: data/groundswellag_sessions_handpicked.csv)
- CSV with speaker bios (default: data/groundswellag_speakers.csv)

**Output:**
- CSV file with enhanced speaker and session information, including fuzzy-matched bios (default: data/groundswellag_speakers_from_handpicked_sessions.csv)

**Example usage:**
```bash
uv run 2_groundswellag_enhance_speaker_with_sessions.py \
    --all-sessions data/groundswellag_sessions_clean.csv \
    --handpicked data/groundswellag_sessions_handpicked.csv \
    --speakers data/groundswellag_speakers.csv \
    --output data/groundswellag_speakers_from_handpicked_sessions.csv
```

---

## Script: 3_groundswellag_extract_job_info_from_bio.py

**Purpose:**
Extracts job titles, organizations, and search keywords from speaker bios using the Claude API. Fully automates batch submission, polling, downloading, and CSV conversion for LinkedIn profile search preparation.

**Input:**
- CSV file with speaker bios (default: data/groundswellag_speakers_from_handpicked_sessions.csv)

**Output:**
- Intermediate JSONL file with batch results (default: data/groundswellag_speaker_search_terms.jsonl)
- Final CSV file with columns: `organization`, `job_title`, `name`, `search_keywords` (default: data/groundswellag_speaker_search_terms.csv)

**Example usage:**
```bash
uv run 3_groundswellag_extract_job_info_from_bio.py \
    --input data/groundswellag_speakers_from_handpicked_sessions.csv \
    --output data/groundswellag_speaker_search_terms.csv \
    --jsonl data/groundswellag_speaker_search_terms.jsonl
```

---

## DuckDuckGo (ddg) Search Workflow

**Purpose:**
Performs DuckDuckGo searches for the LinkedIn profile info of each speaker using the search terms generated in the previous step.

**Input:**
- CSV file with search terms (default: data/groundswellag_speaker_search_terms.csv)

**Output:**
- CSV file with DuckDuckGo search results (e.g., data/groundswellag_speaker_ddg_results.csv)

**Example usage:**
```bash
uv run 4_scraper.py \
    --mode search
    --input data/groundswellag_speaker_search_terms.csv \
    --output data/groundswellag_speaker_ddg_results.csv
```

---

## Script: 5_parse_ddg.py

**Purpose:**
Automates the parsing of DuckDuckGo search results using the Claude API. Submits a batch job, polls for completion, downloads the results, and converts them to CSV—all in one step.

**Input:**
- CSV file with DuckDuckGo search results (default: data/groundswellag_speaker_ddg_results.csv)

**Output:**
- Intermediate JSONL file with batch results (default: data/groundswellag_speakers_parsed_ddg_results.jsonl)
- Final CSV file with parsed and structured results (default: data/groundswellag_speakers_parsed_ddg_results.csv)

**Example usage:**
```bash
uv run 5_parse_ddg.py \
    --input data/groundswellag_speaker_ddg_results.csv \
    --output data/groundswellag_speakers_parsed_ddg_results.csv \
    --jsonl data/groundswellag_speakers_parsed_ddg_results.jsonl
```

---

## Script: 6_groundswellag_merge_speaker_w_ddg.py

**Purpose:**
Merges the DDG search results for each speaker with the speaker bio and sessions.

**Input:**
- CSV file with parsed DDG results (default: data/groundswellag_speakers_parsed_ddg_results.csv)
- CSV file with session speakers data (default: data/groundswellag_speakers_from_handpicked_sessions.csv)

**Output:**
- Merged CSV file (default: data/groundswellag_speakers_from_handpicked_w_background.csv)

**Example usage:**
```bash
uv run 6_groundswellag_merge_speaker_w_ddg.py \
    --ddg data/groundswellag_speakers_parsed_ddg_results.csv \
    --sessions data/groundswellag_speakers_from_handpicked_sessions.csv \
    --output data/groundswellag_speakers_from_handpicked_w_background.csv
```

---

## Script: 7_groundswellag_score_speakers.py

**Purpose:**
Scores and prioritizes Groundswell Festival speakers for outreach using the Claude API, based on all available session and background data.

**Input:**
- CSV file with merged speaker/session/background data (default: data/groundswellag_speakers_from_handpicked_w_background.csv)

**Output:**
- Intermediate JSONL file with batch results (default: data/groundswellag_speakers_from_handpicked_scored.jsonl)
- Final CSV file with scored and prioritized speakers (default: data/groundswellag_speakers_from_handpicked_scored.csv)

**Example usage:**
```bash
uv run 7_groundswellag_score_speakers.py \
    --input data/groundswellag_speakers_from_handpicked_w_background.csv \
    --output data/groundswellag_speakers_from_handpicked_scored.csv
```

---

## Script: 8_groundswellag_merge_speaker_w_scores.py

**Purpose:**
Merges speaker scoring data with comprehensive speaker profiles.

**Input:**
- CSV file with speaker scores (default: data/groundswellag_speakers_from_handpicked_scored.csv)
- CSV file with comprehensive speaker profiles (default: data/groundswellag_speakers_from_handpicked_w_background.csv)

**Output:**
- Final merged CSV file for prioritized outreach (default: data/groundswellag_speakers_from_handpicked_w_scores.csv)

**Example usage:**
```bash
uv run 8_groundswellag_merge_speaker_w_scores.py \
    --scores data/groundswellag_speakers_from_handpicked_scored.csv \
    --speakers data/groundswellag_speakers_from_handpicked_w_background.csv \
    --output data/groundswellag_speakers_from_handpicked_w_scores.csv
```

---

## Script: 9_groundswellag_generate_messages.py

**Purpose:**
Generates personalized LinkedIn outreach messages for scored Groundswell speakers using their profiles and Claude API batch processing.

**Input:**
- CSV file with scored speakers (default: data/groundswellag_speakers_from_handpicked_w_scores.csv)
- Folder with LinkedIn profiles (default: $HOME/linkedin_data/groundswellag/)

**Output:**
- CSV file with generated LinkedIn outreach messages (default: groundswell_outreach_messages_1.csv)

**Example usage:**
```bash
uv run 9_groundswellag_generate_messages.py \
    --speakers data/groundswellag_speakers_from_handpicked_w_scores.csv \
    --profiles $HOME/linkedin_data/groundswellag/ \
    --output groundswell_outreach_messages_1.csv
```
```





---

## Script: 10_groundswellag_merge_handpicked_with_messages.py

**Purpose:**
Merges the generated outreach messages with the scored and enriched speaker profiles to create a final, comprehensive outreach list.

**Input:**
- CSV file with scored and enriched speaker profiles (default: data/groundswellag_speakers_from_handpicked_w_scores_1.csv)
- CSV file with generated outreach messages (default: data/groundswellag_outreach_messages_1.csv)

**Output:**
- Final, comprehensive outreach CSV (default: data/groundswellag_speakers_with_messages_from_handpicked_sessions_1.csv)

**Example usage:**
```bash
uv run 10_groundswellag_merge_handpicked_with_messages.py \
    --speakers data/groundswellag_speakers_from_handpicked_w_scores_1.csv \
    --messages data/groundswellag_outreach_messages_1.csv \
    --output data/groundswellag_speakers_with_messages_from_handpicked_sessions_1.csv
```

---
