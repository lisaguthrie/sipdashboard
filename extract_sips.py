import pdfplumber
import json
import re
from pathlib import Path
from logger import *
from ai_helper import normalize_focus_group, get_actions_summary

def load_school_index(index_file="school_index.json"):
    """Load school index from JSON file"""
    try:
        with open(index_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log_message(ERROR, f"School index file '{index_file}' not found!")
        return {"high": [], "middle": [], "elementary": []}

def normalize_area(text):
    """Normalize goal area to standard categories"""
    log_message(DEBUG, f"Normalizing area from text: '{text[:50]}'")
    if not text:
        return "Other"
    text_lower = text.lower()
    if 'math' in text_lower or 'algebra' in text_lower:
        return "Math"
    elif 'ela' in text_lower or 'literacy' in text_lower or 'reading' in text_lower or 'writing' in text_lower or 'english language arts' in text_lower:
        return "ELA"
    elif 'sel' in text_lower or 'social' in text_lower or 'emotional' in text_lower or 'belonging' in text_lower or 'attendance' in text_lower:
        return "SEL"
    elif 'science' in text_lower or 'stem' in text_lower:
        return "Science"
    elif 'ninth grade' in text_lower or '9th grade' in text_lower:
        return "9th Grade Success"
    elif 'graduat' in text_lower or 'postsecondary' in text_lower:
        return "Graduation"
    else:
        return "Other"

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_strategies_from_table(table):
    """When given a table of strategies (complete or partial), extract action items and measures"""
    strategies = []
    for row in table:
        if not row or len(row) < 2:
            continue
        first_col = clean_text(str(row[0]) if row[0] else "")
        second_col = clean_text(str(row[1]) if row[1] else "")
        # Look for action items (not headers)
        if first_col and "action" not in first_col.lower():
            if not any(first_col.lower().startswith(marker) for marker in ["priority", "focus", "desired", "current", "strategy", "timeline", "method(s)"]):
                log_message(DEBUG, f"   Found action: {first_col[:50]}")
                strategies.append({
                    "action": first_col,
                    "measures": second_col
                })
    return strategies

def finalize_goal(current_goal, school_name, school_level):
    """Finalize a goal by normalizing its focus group/area and adding it to the list of goals"""
    if current_goal:
        focus = normalize_focus_group(school_name, 
                                      school_level,
                                      current_goal.get("focus_group", ""), 
                                      current_goal.get("focus_area", ""), 
                                      current_goal.get("outcome", ""))
        current_goal["focus_grades"] = focus.get("focus_grades", "All Grades")
        current_goal["focus_student_group"] = focus.get("focus_student_group", "All Students")
        strategies = current_goal.get("strategies", [])
        if len(strategies) == 0:
            strategies = [ current_goal.get("raw_strategies", "") ]
        current_goal["strategies_summarized"] = get_actions_summary(school_name, current_goal.get("outcome", ""), strategies)
        return current_goal
    return None

def extract_goals_from_detailed_tables(pdf, start_page_num, end_page_num, school_name, school_level):
    """Extract goals from detailed Continuous Improvement Priorities tables"""    
    goals = []
    current_goal = None
    in_priorities_section = False
    
    log_message(DEBUG, f"Starting detailed table extraction from page {start_page_num + 1}")
    
    # Scan through pages looking for priorities section
    for page_offset in range(0, end_page_num - start_page_num):  # Limit scan to index-specified page range
        if page_offset + start_page_num >= len(pdf.pages):
            break
        
        try:
            page = pdf.pages[start_page_num + page_offset]
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            log_message(DEBUG, f"Scanning page {start_page_num + page_offset + 1}: found {len(tables)} tables")
        except:
            continue
        
        # Check if we've reached the end of priorities section
        if "state assessment participation" in text.lower():
            log_message(DEBUG, f"Found end marker 'State Assessment Participation' on page {start_page_num + page_offset + 1}")
            break
        
        # Check if we've entered the priorities section
        if not in_priorities_section and "continuous improvement priorities" in text.lower():
            log_message(DEBUG, f"Found 'Continuous Improvement Priorities' on page {start_page_num + page_offset + 1}")
            in_priorities_section = True
        # Keller did something different for their priorities header...
        if not in_priorities_section and "helen keller sip 2025-26 current draft" in text.lower():
            log_message(DEBUG, f"Found school-specific marker for {school_name} on page {start_page_num + page_offset + 1}")
            in_priorities_section = True
        
        if not in_priorities_section:
            continue
        
        # Process tables on this page
        strategies_start_page = 0
        single_page_strategy = False
        log_message(DEBUG, f"Processing {len(tables)} tables on page {start_page_num + page_offset + 1}")
        for table_idx, table in enumerate(tables):
            log_message(DEBUG, f"   Table {table_idx + 1}: {len(table)} rows, {len(table[0]) if table else 0} cols")
            if not table or len(table) == 0:
                log_message(DEBUG, f"   skipping")
                continue
            
            for row_idx, row in enumerate(table):
                log_message(DEBUG, f"     Row {row_idx + 1}: {row}")
                if not row or len(row) == 0:
                    log_message(DEBUG, f"     skipping")
                    continue
                
                # Check for Priority #x header (single column row)
                if len(row) == 1 or (len(row) > 1 and not any(row[1:])):
                    cell_text = clean_text(str(row[0]) if row[0] else "")
                    if cell_text.lower().startswith("priority"):
                        # Save previous goal if exists
                        if current_goal:
                            goals.append(finalize_goal(current_goal, school_name, school_level))
                            log_message(INFO, f"Completed goal {len(goals)}: {current_goal['area']}")
                        
                        # Start new goal
                        current_goal = {
                            "area": "",
                            "focus_group": "",
                            "focus_area": "",
                            "focus_grades": "All Grades",
                            "focus_student_group": "All Students",
                            "outcome": "",
                            "currentdata": "",
                            "raw_strategies": "",
                            "strategies": [],
                            "strategies_summarized": "",
                            "engagement_strategies": ""
                        }
                        strategies_start_page = 0
                        single_page_strategy = False
                        found_action_table = False
                        log_message(INFO, f"Started new goal: {cell_text}")
                        continue
                
                # Process two-column data rows
                if current_goal is not None and len(row) >= 2:
                    label = clean_text(str(row[0]) if row[0] else "").lower()
                    value = clean_text(str(row[1]) if row[1] else "")
                    
                    log_message(DEBUG, f"   Got label: '{label}'")
                    if label in ["priority area"]:
                        current_goal["area"] = normalize_area(value)
                        log_message(DEBUG, f"   Priority Area: {current_goal['area']}")
                    
                    elif label in ["focus grade level(s) and/or student group(s)"]:
                        current_goal["focus_group"] = value
                        log_message(DEBUG, f"   Focus group: {value[:50]}")

                    elif label in ["current data supporting focus area", "data and rationale supporting focus area"]:
                        current_goal["currentdata"] = value
                        log_message(DEBUG, f"   Current Data: {value[:50]}")

                    elif label in ["focus area"]:
                        current_goal["focus_area"] = value
                        log_message(DEBUG, f"   Focus Area: {value[:50]}")
                    
                    elif label in ["desired outcome"]:
                        current_goal["outcome"] = value
                        log_message(DEBUG, f"   Outcome: {value[:50]}")
                    
                    elif label in ["strategy to address priority"]:
                        # The value cell associated with this label contains an embedded table. We'll process the table
                        # separately. Here, we just save the page where it starts.
                        strategies_start_page = start_page_num + page_offset

                        # The value cell typically contains an embedded table with the list of actions and measures. 
                        # We process the embedded table separately. But sometimes, there is no embedded table, it's just text
                        # in the cell, in which case the logic to process the embedded table never runs. So we'll save off
                        # the raw text in the cell for now, and figure out later whether we need it.
                        current_goal["raw_strategies"] = value

                    elif label in ["strategy to engage students, families, parents and community members", "strategy to engage students, families, parents and communit y members"]:
                        # This is the row immediately following the "Strategy to Address Priority" row. If it appears on
                        # the same page as the start of the strategy table, then we know the latter is contained on one
                        # page. Make a note of it for when we go to process it later.
                        if strategies_start_page == start_page_num + page_offset:
                            single_page_strategy = True
                            log_message(DEBUG, f"   Detected single-page strategy table starting on page {strategies_start_page + 1}")
                        
                        # Add the engagement strategy (different from the actions table) to the current goal.
                        current_goal["engagement_strategies"] = value

                    elif label in ["timeline for focus"]:
                        # All schools are *supposed* to have the engagement strategy row... but some don't. So we need to do the
                        # same logic around checking for whether there's a single-page strategy table here as well.
                        if strategies_start_page == start_page_num + page_offset:
                            single_page_strategy = True
                            log_message(DEBUG, f"   Detected single-page strategy table starting on page {strategies_start_page + 1}")

                    elif label == "action" and value.lower() == "measure of fidelity of implementation":
                        current_goal["raw_strategies"] = ""  # Clear raw strategies. We won't need it since we've found the embedded table with strategies.
                        # Get all the strategies out of the current table.
                        strategies = extract_strategies_from_table(table)

                        # This table may span multiple pages. Or, it might not.
                        if single_page_strategy:
                            log_message(DEBUG, f"   Single-page strategy table had {len(strategies)} strategies")
                            current_goal["strategies"] = strategies
                            continue

                        # Pick up on the next page and scan ahead.
                        for scan_offset in range(1, end_page_num - start_page_num):  # Limit scan to index-specified page range
                            if start_page_num + page_offset + scan_offset >= end_page_num or start_page_num + page_offset + scan_offset >= len(pdf.pages):
                                log_message(INFO, f"   Reached end of page range while scanning for strategy table continuation")
                                break
                            try:
                                scan_page = pdf.pages[start_page_num + page_offset + scan_offset]
                                scan_tables = scan_page.extract_tables() or []
                                log_message(DEBUG, f" got {len(scan_tables)} tables on scan page {start_page_num + page_offset + scan_offset + 1}")
                                
                                # Scenario #2: The embedded Action table continues onto the next page. In this case, 
                                # the first table will be the outer table. The first row will have an empty first cell,
                                # and the embedded table in the second cell. 
                                # The second table will be the continuation of the Action table.
                                if (scan_tables[0][0][0] == "" and len(scan_tables) > 1):
                                    continuation = scan_tables[1]

                                    # Scenario #2a: The page break splits a row in the table. We can easily detect the
                                    # case where either the first or second cell is empty, and merge it with the last
                                    # item from the previous page. 
                                    # TODO: Scenario #2b: Unfortunately, it's also possible that the first and
                                    # second cell will both have items in them, and that's harder to detect.
                                    if continuation[0][0] == "" or continuation[0][1] == "":
                                        strategies[-1]["action"] += " " + clean_text(str(continuation[0][0]))
                                        strategies[-1]["measures"] += " " + clean_text(str(continuation[0][1]))
                                        log_message(DEBUG, f"   Merged split row from page {start_page_num + page_offset + scan_offset + 1}")
                                        # Remove the continuation row since we merged it
                                        continuation = continuation[1:]

                                    strategies.extend(extract_strategies_from_table(scan_tables[1]))

                                    # If the outer table has multiple rows, i.e. there are rows after the row containing
                                    # the continued Action table, then we know we've found the end of the Action table.
                                    if (len(scan_tables[0]) > 1):
                                        break

                                    # Otherwise, we'll move on to the next page.

                                # TODO: Scenario #3: The embedded Action table ended at the very end of the previous page.
                            except Exception as e:
                                log_message(ERROR, f"Error processing '{school_name}' scan page {start_page_num + page_offset + scan_offset + 1}: {e}")
                                pass
                        
                        if strategies:
                            current_goal["strategies"] = strategies
                            log_message(DEBUG, f"   Strategies: {len(strategies)} found")
                    elif len(row) == 2 and label == "" and current_goal["raw_strategies"] != "":
                        current_goal["raw_strategies"] += " " + value
                        log_message(DEBUG, f"   Got strategy text without table: '{value[:50]}'")
                    
                    else:
                        log_message(DEBUG, f" UNRECOGNIZED LABEL: '{label}' with value: '{value[:50]}'")

    # Save final goal
    if current_goal:
        goals.append(finalize_goal(current_goal, school_name, school_level))
        log_message(INFO, f"Completed final goal {len(goals)}: {current_goal['area']}")
    
    return goals

def find_school_in_pdf(pdf_path, school_name, level_name, start_page, end_page):
    """Find a specific school and extract its SIP data using page range from index"""
    log_message(INFO, f"  Extracting '{school_name}' from pages {start_page}-{end_page}...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Validate page range
            if start_page - 1 >= len(pdf.pages):
                log_message(ERROR, f"    Start page {start_page} exceeds PDF length ({len(pdf.pages)} pages)")
                return None
            
            # Convert to 0-indexed
            page_idx = start_page - 1
            
            try:
                page = pdf.pages[page_idx]
                text = page.extract_text() or ""
                
                # Verify school is on this page
                if school_name.lower() not in text.lower():
                    log_message(WARNING, f"    School name '{school_name}' not found on page {start_page}")
            except:
                log_message(ERROR, f"    Error reading page {start_page}")
                return None
            
            # Extract goals using detailed table format
            goals = extract_goals_from_detailed_tables(pdf, page_idx, end_page - 1, school_name, level_name)
            
            if len(goals) >= 3:
                log_message(INFO, f"    Extracted {len(goals)} goals for '{school_name}'")
                return {
                    "name": school_name,
                    "level": level_name,
                    "goals": goals[:3]  # Take first 3 goals
                }
            else:
                log_message(WARNING, f"    Only found {len(goals)} goals for '{school_name}'")
                if goals:
                    return {
                        "name": school_name,
                        "level": level_name,
                        "goals": goals
                    }
                return None
                
    except Exception as e:
        log_message(ERROR, f"  Error processing '{school_name}': {e}")
        return None

def extract_all_schools():
    """Extract SIP data for all schools using school_index.json"""
    # Load school index
    school_index = load_school_index("school_index.json")
    
    pdf_dir = Path(".")
    pdf_files = {
        "Elementary School": pdf_dir / "Elementary School 2025-2026 SIPs.pdf",
        "Middle School": pdf_dir / "Middle School 2025-2026 SIPs.pdf",
        "High School": pdf_dir / "High School 2026-2026 SIPs.pdf"
    }
    
    all_schools = []
    found_schools = []
    missing_schools = []
    
    # Map index levels to PDF file keys
    level_map = {
        "elementary": "Elementary School",
        "middle": "Middle School",
        "high": "High School"
    }
    
    # Process each school level from index
    for level_key, level_name in level_map.items():
        if level_key not in school_index:
            log_message(WARNING, f"Level '{level_key}' not found in school index")
            continue
        
        schools_list = school_index[level_key]
        pdf_path = pdf_files[level_name]
        
        log_message(INFO, "\n" + "="*80)
        log_message(INFO, f"EXTRACTING {level_name.upper()} SCHOOLS ({len(schools_list)} schools)")
        log_message(INFO, "="*80)
        
        if not pdf_path.exists():
            log_message(ERROR, f"PDF file not found: {pdf_path}")
            for school_info in schools_list:
                missing_schools.append(f"{school_info['school']} ({level_name})")
            continue
        
        for school_info in schools_list:
            school_name = school_info["school"]
            start_page = school_info["start"]
            end_page = school_info["end"]
            
            result = find_school_in_pdf(pdf_path, school_name, level_name, start_page, end_page)
            if result:
                all_schools.append(result)
                found_schools.append(f"{school_name} ({level_name})")
            else:
                missing_schools.append(f"{school_name} ({level_name})")
                log_message(WARNING, f"  [EXTRACTION FAILED]: {school_name}")
    
    # Save results
    output_file = "schools_extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_schools, f, indent=2, ensure_ascii=False)
    
    # Print summary
    log_message(INFO, "\n" + "="*80)
    log_message(INFO, "EXTRACTION SUMMARY")
    log_message(INFO, "="*80)
    log_message(INFO, f"Successfully extracted: {len(found_schools)} schools")
    log_message(INFO, f"Failed to extract: {len(missing_schools)} schools")
    log_message(INFO, f"\nOutput file: {output_file}")
    
    if found_schools:
        log_message(INFO, "\n[SUCCESSFULLY EXTRACTED]:")
        for school in sorted(found_schools):
            log_message(INFO, f"  - {school}")
    
    if missing_schools:
        log_message(ERROR, "[FAILED TO EXTRACT]:")
        for school in sorted(missing_schools):
            log_message(ERROR, f"  - {school}")
    
    return all_schools

if __name__ == "__main__":
    school_index = load_school_index("school_index.json")
    total_schools = sum(len(schools) for schools in school_index.values())
    log_message(INFO, f"Starting SIP extraction using school_index.json...")
    log_message(INFO, f"Total schools to extract: {total_schools}")
    extract_all_schools()
