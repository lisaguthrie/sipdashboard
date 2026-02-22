# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a School Improvement Plan (SIP) data extraction and analysis system that:
1. Extracts structured data from PDF SIP documents for school districts
2. Uses Claude AI to normalize and summarize the extracted data
3. Provides a React-based dashboard for visualization, search, and AI-powered Q&A

## Common Commands

### Running the Extraction Pipeline
```bash
# Extract all schools from PDFs using the school index
python extract_sips.py

# This will generate:
# - schools_extracted.json (structured goal data)
# - goals_embeddings.json (vector embeddings for semantic search)

# Parse school index from text to JSON (if needed)
python parse_school_index.py

# Build embeddings separately (if needed)
python vector_store.py

# Test semantic search from command line
python vector_store.py "math interventions for third grade"
```

### Testing
```bash
# Run all tests
pytest

# Run a specific test file
pytest test_prompts.py
pytest test_json_loading.py
pytest test_vector_store.py

# Run with verbose output
pytest -v
```

### Environment Setup
- Create a `.env` file with `ANTHROPIC_API_KEY=your_api_key_here`
- Install dependencies: `pip install -r requirements.txt`
- Required Python packages: `pdfplumber`, `anthropic`, `sentence-transformers`, `chromadb`, `numpy`, `pytest`, `python-dotenv`

## Architecture

### Data Flow

```
PDF Files → extract_sips.py → AI Normalization → schools_extracted.json → React Dashboard
    ↑              ↓                    ↓                       ↓
school_index.json  ↓              ai_helper.py          vector_store.py
                   ↓              prompts.py                   ↓
              pdfplumber           Claude API          goals_embeddings.json
                                                              ↓
                                                    (Semantic Search in Dashboard)
```

### Core Components

**extract_sips.py** - Main extraction engine
- Uses `school_index.json` to map schools to PDF page ranges
- Extracts goals from complex table structures that may span multiple pages
- Key challenge: Tables can be nested (outer goal definition table with embedded action/measures table)
- Handles page breaks that can split table rows mid-content
- Normalizes goal areas (Math, ELA, SEL, etc.) and calls AI for focus group normalization
- Generates vector embeddings for semantic search using `vector_store.py`
- Outputs structured JSON with 3 goals per school: `schools_extracted.json` and `goals_embeddings.json`

**vector_store.py** - Vector embeddings for semantic search
- Generates embeddings for all goals using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Creates searchable text from goal fields: outcome, focus_area, full strategies text (actions + measures)
- Exports `goals_embeddings.json` with pre-computed vectors and metadata
- Enables semantic search without requiring a backend server
- Supports filtering by area, school_level, focus_grades, focus_student_group
- Can be run standalone or called automatically during extraction

**ai_helper.py** - AI-powered data normalization
- Two main functions:
  1. `normalize_focus_group()` - Extracts structured focus grades and student groups from raw text
  2. `get_actions_summary()` - Generates natural language summaries of action items
- Smart caching: First checks `schools_extracted.json` for previously normalized data before calling API
- Uses Claude Haiku for cost efficiency with prompt caching for the system prompt
- Graceful fallback to defaults ("All Grades", "All Students") on error

**prompts.py** - Prompt templates for Claude API
- Contains system prompt with examples for focus group normalization
- Defines the valid output categories (focus_grades, focus_student_group)
- Uses few-shot examples to guide the model

**logger.py** - Simple logging system
- Log levels: DEBUG, INFO, WARNING, ERROR
- Set `LOGLEVEL` to control verbosity (default: INFO)

### School Index Structure

`school_index.json` contains page ranges for each school in the PDFs:
```json
{
  "high": [{"school": "Name", "start": 1, "end": 10}, ...],
  "middle": [...],
  "elementary": [...]
}
```

Page numbers are 1-indexed (as they appear in PDF viewers).

### Output Data Structure

`schools_extracted.json` contains:
```json
[
  {
    "name": "School Name",
    "level": "Elementary School|Middle School|High School",
    "goals": [
      {
        "area": "Math|ELA|SEL|Science|9th Grade Success|Graduation|Other",
        "focus_group": "Raw text from SIP",
        "focus_area": "Raw text from SIP",
        "focus_grades": "All Grades|Grade X|Grades X-Y",
        "focus_student_group": "All Students|Low Income|ML|Special Education|Race/Ethnicity",
        "outcome": "Desired outcome text",
        "currentdata": "Current data supporting focus",
        "strategies": [{"action": "...", "measures": "..."}],
        "strategies_summarized": "AI-generated summary",
        "engagement_strategies": "Text"
      }
    ]
  }
]
```

## Key Implementation Details

### PDF Table Extraction Challenges

The SIP PDFs use nested table structures:
1. **Outer table**: Contains goal metadata (Priority Area, Focus Area, Outcome, etc.)
2. **Embedded action table**: Lives in a cell of the outer table with columns: Action | Measure of Fidelity

**Page break scenarios handled:**
- **Scenario 1**: Single-page action table (detected when engagement strategy row appears on same page)
- **Scenario 2**: Action table continues to next page (first cell empty, embedded table in second cell, continuation table follows)
- **Scenario 2a**: Page break splits a row (detected when first or second cell is empty on continuation page)

See `extract_strategies_from_table()` and `extract_goals_from_detailed_tables()` for implementation.

### AI Normalization Strategy

The system minimizes API costs by:
1. **JSON cache-first**: Always check `schools_extracted.json` for exact matches (school + focus_group + focus_area + outcome)
2. **Prompt caching**: System prompt is marked for ephemeral caching (saves ~90% on repeated calls)
3. **Cheap model**: Uses Claude Haiku (fast + inexpensive) instead of Sonnet
4. **Fallback gracefully**: Returns defaults instead of failing on API errors

### Testing Philosophy

Tests use `use_ai=False` parameter to avoid API calls during testing. The `set_client()` function in `ai_helper.py` allows injecting mock clients for unit tests.

### Vector Store and Semantic Search

The system generates vector embeddings for semantic search capabilities:

**Architecture:**
- Pre-computed embeddings during extraction (server-side)
- Exported as `goals_embeddings.json` (~5-10MB for 150 goals)
- Designed for client-side search in Claude artifacts (no backend required)
- Uses `sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions)

**Embeddings file structure:**
```json
{
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimensions": 384,
  "goals": [
    {
      "id": "school-level-goal-1-area",
      "school_name": "School Name",
      "school_level": "Elementary School",
      "area": "Math",
      "embedding": [0.123, -0.456, ...],  // 384-dim vector
      "content": {
        "outcome": "...",
        "focus_area": "...",
        "strategies_summarized": "..."
      }
    }
  ]
}
```

**Dashboard integration (future):**
- User uploads both JSON files to artifact storage
- Dashboard uses transformers.js (@xenova/transformers) to embed queries in-browser
- Computes cosine similarity client-side against pre-computed vectors
- Returns top-k most relevant goals for RAG with Claude
- Reduces token usage by ~90% vs sending all schools

## React Dashboard

**SIPDashboard.jsx** - Frontend visualization
- Loads data from persistent storage API (`window.storage`)
- Features:
  - Overview stats with charts (Recharts library)
  - Search and filtering by school level and goal area
  - Detailed school view modal with expandable goals
  - AI chat interface for natural language queries
  - Export to HTML table
- Uses shared storage for school data (multi-user) and personal storage for chat history

## Important Notes

- **School index accuracy**: `school_index.json` may need manual correction if PDF page ranges don't match actual content
- **Log level**: Set `logger.LOGLEVEL = logger.DEBUG` in your script to see detailed extraction progress
- **API key**: Required in `.env` for extraction to work; tests can run without it using `use_ai=False`
- **Goal limit**: System extracts up to 3 goals per school (hard-coded in `find_school_in_pdf()`)