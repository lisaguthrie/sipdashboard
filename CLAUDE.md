# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a School Improvement Plan (SIP) data extraction and analysis system with:
1. **Python extraction pipeline** - Extracts structured data from PDF SIP documents
2. **AI-powered normalization** - Uses Claude AI to normalize and summarize extracted data
3. **React + Vite frontend** - Modern web dashboard with charts, search, and filtering
4. **FastAPI backend** - Provides semantic search (RAG) and AI chat capabilities
5. **Azure deployment** - Containerized deployment via GitHub Actions to Azure Container Apps

## Common Commands

### Development Setup

**Python backend dependencies:**
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**React frontend dependencies:**
```bash
cd dashboard
npm install
```

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

### Running the Web Application

**Start the FastAPI backend server:**
```bash
cd server
# Ensure .env file exists with ANTHROPIC_API_KEY=your_key
uvicorn main:app --reload --port 8000
```

**Start the React development server:**
```bash
cd dashboard
# Create .env.local with: VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

The dashboard will be available at `http://localhost:5173` (or the port shown in terminal).

**Build for production:**
```bash
cd dashboard
npm run build
# Output goes to dashboard/dist/

# To preview production build:
npm run preview
```

### Environment Setup
- Root `.env` and `server/.env` require `ANTHROPIC_API_KEY=your_api_key_here`
- `dashboard/.env.local` (for local dev) requires `VITE_API_BASE_URL=http://localhost:8000`
- Root dependencies: `pip install -r requirements.txt` (for extraction scripts)
- Server dependencies: `pip install -r server/requirements.txt` (for API server)
- Dashboard dependencies: `npm install` in dashboard directory

## Architecture

### Data Flow

```
┌─────────────────── EXTRACTION PIPELINE (Python) ────────────────────┐
│                                                                      │
│  PDF Files → extract_sips.py → AI Normalization → schools_extracted.json
│      ↑              ↓                    ↓
│  school_index.json  ↓              ai_helper.py
│                     ↓              prompts.py
│                 pdfplumber         Claude API
│
│  vector_store.py → goals_embeddings.json
│
└──────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────── WEB APPLICATION ───────────────────────┐
│                                                               │
│  React Frontend (dashboard/)         FastAPI Backend (server/)
│  ├─ App.jsx (main component)        ├─ main.py (API server)
│  ├─ Charts & visualizations         ├─ RAG retrieval
│  ├─ Search & filtering              ├─ Semantic search
│  └─ AI chat interface ──────HTTP────┴─ Claude API proxy
│                                      │
│                                      └─ Loads goals_embeddings.json
│
└───────────────────────────────────────────────────────────────┘
                            ↓
                   Azure Container Apps
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

### Web Application Components

**dashboard/src/App.jsx** - React frontend
- Built with Vite, React 19, Tailwind CSS
- Recharts for data visualization (pie charts, bar charts)
- Lucide React for icons
- Features:
  - Overview statistics with charts showing goal area distribution
  - Focus group statistics (ML, Low Income, Special Ed, etc.)
  - Trend analysis identifying common themes (ML focus, sense of belonging)
  - Search and multi-level filtering (school name, level, goal area)
  - School detail modal with expandable goal cards
  - AI chat interface with conversation history
  - Export to HTML table
- Uses localStorage for data persistence and chat history
- Calls `/api/chat` endpoint on backend for AI Q&A

**server/main.py** - FastAPI backend server
- Provides RAG (Retrieval-Augmented Generation) for AI chat
- Loads `goals_embeddings.json` from CDN on startup
- Uses `sentence-transformers/all-MiniLM-L6-v2` for query embedding
- Retrieves top-k most relevant goals via cosine similarity
- Calls Claude Sonnet 4 API with conversation history and retrieved context
- Uses prompt caching to reduce API costs (~90% savings on repeated context)
- Serves static React build files for production deployment
- CORS enabled for local development

**server/Dockerfile** - Container image for deployment
- Multi-stage build optimizing for size
- Copies React build into `server/static/`
- Installs Python dependencies and downloads embedding model
- Exposes port 8000, runs via uvicorn

**.github/workflows/deploy.yml** - CI/CD pipeline
- Triggered on push to main branch
- Builds React frontend with production environment variables
- Copies build output to `server/static/`
- Builds Docker image and pushes to Azure Container Registry
- Deploys to Azure Container Apps with secret management for API key

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
- Pre-computed embeddings during extraction using `vector_store.py`
- Exported as `goals_embeddings.json` (~5-10MB for 150 goals)
- Uses `sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions)
- Backend server loads embeddings from CDN on startup for zero-latency search

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
      "text": "School name: ...\nGoal #1 ...",  // Full text for RAG context
      "content": {
        "outcome": "...",
        "focus_area": "...",
        "strategies_summarized": "..."
      }
    }
  ]
}
```

**RAG implementation (backend):**
- FastAPI server embeds user question using same model
- Computes cosine similarity against all goal embeddings (batch dot product)
- Returns top-k (default 10) most relevant goal texts
- Injects retrieved context into Claude API system prompt with cache control
- Prompt caching reduces token costs by ~90% when context doesn't change
- Critical attribution rules in system prompt prevent school misattribution

## Deployment

### Local Development
1. Start backend: `cd server && uvicorn main:app --reload`
2. Start frontend: `cd dashboard && npm run dev`
3. Frontend proxies API calls to `http://localhost:8000` (configured via `.env.local`)

### Production Deployment (Azure)
The project uses GitHub Actions for automated deployment to Azure Container Apps:

**Prerequisites:**
- Azure Container Registry (ACR) created
- Azure Container App created with managed identity
- GitHub secrets configured:
  - `AZURE_CREDENTIALS` - Service principal JSON for Azure login
  - `VITE_API_BASE_URL` - Empty string (API served from same origin)
- Container App secret `anthropic-api-key` configured

**Deployment flow:**
1. Push to main branch triggers workflow
2. GitHub Actions builds React app with production env vars
3. Copies build to `server/static/`
4. Builds Docker image with both frontend and backend
5. Pushes to Azure Container Registry
6. Deploys new image to Azure Container Apps

**Architecture notes:**
- Single container serves both React static files and API
- FastAPI serves React SPA on all non-API routes
- Embedding model and goals JSON loaded once at container startup
- Horizontal scaling possible (model loaded in each instance)

### Manual Deployment
```bash
# Build React app
cd dashboard
npm run build

# Copy to server static directory
mkdir -p ../server/static
cp -r dist/. ../server/static/

# Build and run Docker container locally
cd ../server
docker build -t sip-dashboard .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_key sip-dashboard
```

## Important Notes

### Extraction Pipeline
- **School index accuracy**: `school_index.json` may need manual correction if PDF page ranges don't match actual content
- **Log level**: Set `logger.LOGLEVEL = logger.DEBUG` in your script to see detailed extraction progress
- **API key**: Required in `.env` for extraction to work; tests can run without it using `use_ai=False`
- **Goal limit**: System extracts up to 3 goals per school (hard-coded in `find_school_in_pdf()`)

### Web Application
- **API key security**: Never commit `.env` files; use GitHub secrets for deployment
- **CORS**: Backend allows all origins in dev; tighten for production by modifying `server/main.py`
- **Embeddings CDN**: Backend fetches embeddings from GitHub CDN on startup (configured in `server/main.py`)
- **localStorage limits**: Browser localStorage has ~5-10MB limit; works fine for 50 schools
- **Chat history**: Stored in browser localStorage; cleared only when user clicks "Clear Chat"
- **Model downloads**: First container startup downloads ~100MB sentence-transformers model
- **Prompt caching**: Backend uses Claude's ephemeral caching to reduce costs; cache TTL is 5 minutes