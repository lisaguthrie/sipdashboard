# School Improvement Plan Dashboard

An intelligent data extraction and visualization system for analyzing School Improvement Plans (SIPs) across an entire school district.

## Problem Statement

School boards are legally required to approve School Improvement Plans for all schools in their district. With 50+ schools each submitting 5-10 page documents, this creates a significant challenge:

- **Too much information**: Hundreds of pages of dense text make meaningful review nearly impossible
- **Inconsistent formats**: Free-form text makes it difficult to identify patterns or compare across schools
- **Limited analysis**: Traditional review processes don't allow for cross-cutting questions like "Which schools are focusing on multilingual learners?" or "What are common SEL strategies?"

The result is that SIP approval often becomes a check-the-box exercise rather than meaningful oversight.

## Solution

This project provides:

1. **Automated data extraction** from PDF SIP documents into structured JSON
2. **AI-powered normalization** to standardize goal descriptions and focus groups
3. **Interactive dashboard** with search, filtering, visualizations, and AI-powered Q&A

The system transforms hundreds of pages of unstructured text into actionable insights, enabling school board directors to:
- Quickly understand priorities across all schools
- Identify district-wide trends and patterns
- Ask natural language questions about the SIPs
- Export data for further analysis or reporting

## Features

### Data Extraction Pipeline

- Extracts structured data from PDF SIP documents
- Handles complex nested table structures and multi-page tables
- Normalizes goal areas (Math, ELA, SEL, Science, etc.)
- Uses Claude AI to identify target grades and student groups (e.g., "ML", "Low Income", "Special Education")
- Generates natural language summaries of action items

### Interactive Dashboard

- **Overview Statistics**: Quick view of total schools, goals, and focus areas
- **Visual Analytics**: Charts showing distribution of goal areas and focus groups
- **Trend Analysis**: Automatic identification of common themes (e.g., multilingual learner focus, belonging initiatives)
- **Search & Filter**: Find schools by name, level, or goal content
- **Detailed View**: Expandable goal cards showing outcomes and strategies
- **AI Chat Interface**: Ask questions about the SIPs using natural language
- **Export**: Generate HTML tables for reports or presentations

## Project Structure

```
sipdashboard/
├── extract_sips.py           # Main extraction engine
├── ai_helper.py              # AI normalization functions
├── prompts.py                # Claude API prompt templates
├── logger.py                 # Simple logging system
├── parse_school_index.py     # Utility to parse school index
├── school_index.json         # Maps schools to PDF page ranges
├── schools_extracted.json    # Structured output data (full fidelity)
├── schools_extracted.txt     # Flat text format used by the dashboard AI Q&A
├── SIPDashboard.jsx          # React dashboard component
├── test_prompts.py           # Unit tests for AI functions
├── test_json_loading.py      # Integration tests
├── *.pdf                     # Source SIP documents
└── .env                      # API key configuration
```

## Getting Started

### Prerequisites

- Python 3.8+
- Anthropic API key
- PDF SIP documents organized by school level

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sipdashboard
   ```

2. **Install Python dependencies**
   ```bash
   pip install pdfplumber anthropic python-dotenv pytest
   ```

3. **Configure environment**

   Create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Prepare school index**

   Create or update `school_index.json` with page ranges for each school:
   ```json
   {
     "elementary": [
       {"school": "Franklin Elementary", "start": 1, "end": 8},
       {"school": "Lincoln Elementary", "start": 9, "end": 16}
     ],
     "middle": [...],
     "high": [...]
   }
   ```

   You can use `parse_school_index.py` to convert a text index to JSON format.

### Usage

#### Extract Data from PDFs

```bash
python extract_sips.py
```

This will:
1. Read `school_index.json` to find page ranges
2. Extract goals from each school's SIP
3. Normalize data using Claude AI
4. Save results to `schools_extracted.json` (full structured data)
5. Generate `schools_extracted.txt` (flat text format optimized for AI Q&A)

**Note**: Set log level to DEBUG for detailed output:
```python
import logger
logger.LOGLEVEL = logger.DEBUG
```

#### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_prompts.py

# Verbose output
pytest -v
```

#### Deploy Dashboard

The dashboard is designed to run as a **Claude artifact** — paste the contents of `SIPDashboard.jsx` directly into a Claude conversation and ask Claude to render it. This is required because:

- The AI Q&A feature calls the Anthropic API directly from the browser, which only works within the Claude artifact sandbox (CORS restrictions block these calls from regular browsers)
- Data persistence uses `window.storage`, which is Claude's artifact storage API

The dashboard will not function correctly if hosted as a standalone web page or integrated into a regular React application without a backend proxy for the AI Q&A feature.

#### Load Data into the Dashboard

After running extraction, you need to upload the school data into the dashboard. There are two files to load:

1. **`schools_extracted.json`** — Powers the overview stats, charts, search/filter, and detailed school cards. Paste the full contents of this file into the "Paste JSON data" field in the dashboard's data upload screen.

2. **`schools_extracted.txt`** — Powers the AI Q&A chat interface. This flat text format is optimized for LLM accuracy (each goal entry explicitly names its school, reducing misattribution errors). Paste the full contents of this file into the "Paste TXT data" field.

Both fields must be filled in for all dashboard features to work. Once uploaded, the data is persisted via Claude's shared storage and does not need to be re-uploaded in future sessions.

## Data Structure

### Output: Flat Text for AI Q&A (`schools_extracted.txt`)

The flat text file is used by the dashboard's AI chat interface. Each goal is a self-contained block that explicitly names the school on every entry, which helps the LLM correctly attribute information to the right school when answering questions:

```text
School: Alcott Elementary (Elementary School)
Goal #1 (ELA, All Grades, ML): 70% of ML students will score Low/Minimal Risk on Spring 2028 FastBridge aReading.
Focus Area: Literacy Growth
Current Data: 50% of ML students scored Low/Minimal Risk on Spring 2025 FastBridge aReading.
Strategies:
 * Action: K-2 staff using Heggerty Phonemic Awareness Curriculum.
   Measures: Yearly use review.
 * Action: K-2 staff using UFLI Curriculum.
   Measures: Yearly use review.
...

School: [Next School Name] (Level)
Goal #1 (...): ...
```

### Input: School Index

Maps each school to its page range in the PDF documents:

```json
{
  "elementary": [
    {
      "school": "School Name",
      "start": 1,
      "end": 10
    }
  ]
}
```

### Output: Extracted Schools

Structured JSON with normalized goal data:

```json
[
  {
    "name": "School Name",
    "level": "Elementary School",
    "goals": [
      {
        "area": "Math",
        "focus_grades": "Grades 3-5",
        "focus_student_group": "Low Income",
        "focus_area": "Raw text describing focus",
        "focus_group": "Raw text describing target group",
        "outcome": "Desired outcome text",
        "currentdata": "Supporting data",
        "strategies": [
          {"action": "Action item", "measures": "Fidelity measures"}
        ],
        "strategies_summarized": "AI-generated summary paragraph",
        "engagement_strategies": "Family/community engagement approach"
      }
    ]
  }
]
```

## Technical Details

### PDF Extraction Challenges

The SIP documents use nested table structures:
- **Outer table**: Contains goal metadata (Priority Area, Focus Area, Outcome, etc.)
- **Embedded table**: Action items and measures nested within a cell

The extraction engine handles:
- Tables spanning multiple pages
- Page breaks that split rows mid-content
- Varying table formats across schools

### AI Optimization

To minimize API costs, the system:
1. **Cache-first lookup**: Checks `schools_extracted.json` for previously normalized data
2. **Prompt caching**: Uses Claude's ephemeral caching for system prompts (~90% cost savings on repeated calls)
3. **Efficient model**: Uses Claude Haiku for normalization (fast and cost-effective)
4. **Graceful fallbacks**: Returns defaults instead of failing on API errors

### Cost Estimate

With current implementation:
- ~50 schools × 3 goals = 150 API calls for initial extraction
- Prompt caching reduces costs significantly on re-runs
- Estimated cost: $0.50-$2.00 for full district extraction (first run)
- Re-runs with cache: $0.10-$0.50

## Development

### Running Tests

The test suite uses `use_ai=False` to avoid API calls:

```python
# Test without AI (uses defaults or JSON cache)
result = normalize_focus_group(
    school_name="Test School",
    school_level="Elementary School",
    focus_group="K-5",
    focus_area="Math",
    outcome="Increase scores",
    use_ai=False
)
```

### Debugging

Enable debug logging to see detailed extraction progress:

```python
from logger import *
log_message(DEBUG, "Your debug message")

# Or set globally
import logger
logger.LOGLEVEL = logger.DEBUG
```

## Troubleshooting

### "School name not found on page"

The page range in `school_index.json` may be incorrect. Manually verify the PDF page numbers and update the index.

### "Only found N goals"

Some schools may have fewer than 3 goals or the extraction failed. Check:
1. Does the school use the standard SIP template?
2. Are the tables properly formatted in the PDF?
3. Run with DEBUG logging to see where extraction stopped

### API Errors

If AI normalization fails:
- Verify `ANTHROPIC_API_KEY` is set correctly in `.env`
- Check API quota/billing status
- The system will fall back to defaults ("All Grades", "All Students")

## Use Cases

### For School Board Directors

- Review all SIPs in minutes instead of hours
- Ask questions like "Which schools are focusing on math for low-income students?"
- Identify alignment with district strategic priorities
- Export data for board presentations

### For District Leadership

- Identify trends across schools
- Find schools with similar goals for collaboration opportunities
- Monitor implementation of district initiatives
- Track focus on specific student populations

### For Principals

- See how your SIP compares to other schools
- Find schools with similar goals for best practice sharing
- Verify your SIP data was extracted correctly

## Future Enhancements

- Progress tracking against SIP goals throughout the year
- Historical comparison across years
- Automatic alignment checking with board policies
- Integration with student outcome data
- School-level dashboards for principals

## Contributing

This project was created for a specific school district's needs but can be adapted for other districts with similar SIP formats.

## License

[Specify your license here]

## Acknowledgments

Built with:
- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF extraction
- [Anthropic Claude](https://www.anthropic.com) for AI-powered normalization
- [Recharts](https://recharts.org) for visualizations

---

**Questions or Issues?** Open an issue or contact the maintainer.
