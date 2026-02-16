import json
import re

def parse_school_index(filepath):
    """
    Parse school_index.txt and rewrite the information in JSON format. Note that the index file itself may not be correct (i.e. it may not correspond to the actual SIP files) but at least it gives a good starting point for manual edits.
    """
    schools = {
        "high": [],
        "middle": [],
        "elementary": []
    }
    
    current_level = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Identify section headers
            match = re.match(r'Appendix: ([\w]+) School', line)
            if match:
                level = match.group(1).lower()
                if level in schools:
                    current_level = level
                else:
                    current_level = None
                continue
            
            # Match school name with page range
            # Example: Eastlake High School pp. 1-9
            match = re.match(r'(.+?)\s+pp\.\s*(\d+)\s*[-]\s*(\d+)', line)
            if match:
                school_name = match.group(1).strip()
                start_page = int(match.group(2))
                end_page = int(match.group(3))
                
                if current_level:
                    schools[current_level].append({
                        "school": school_name,
                        "start": start_page,
                        "end": end_page
                    })
    
    return schools

def main():
    input_file = "school_index.txt"
    output_file = "school_index.json"
    
    # Parse the file
    schools_data = parse_school_index(input_file)
    
    # Write to JSON
    with open(output_file, 'w') as f:
        json.dump(schools_data, f, indent=4)
    
    print(f"✓ Successfully parsed {input_file}")
    print(f"✓ Output written to {output_file}")
    print(f"\nSummary:")
    print(f"  High Schools: {len(schools_data['high'])}")
    print(f"  Middle Schools: {len(schools_data['middle'])}")
    print(f"  Elementary Schools: {len(schools_data['elementary'])}")

if __name__ == "__main__":
    main()