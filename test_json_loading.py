"""
Quick test to verify JSON loading functionality in ai_helper.py
"""
from ai_helper import normalize_focus_group
import logger
import json

# Set log level to DEBUG to see debug messages
logger.LOGLEVEL = logger.DEBUG

# Load the actual data from the JSON file for testing
with open('schools_extracted.json', 'r', encoding='utf-8') as f:
    schools = json.load(f)

# Get the first goal from Alcott Elementary
alcott = next(s for s in schools if s['name'] == 'Alcott Elementary')
first_goal = alcott['goals'][0]

# Test 1: Load from JSON with exact match (use_ai=False)
print("Test 1: Loading from JSON with use_ai=False (exact match)")
result = normalize_focus_group(
    school_name=alcott['name'],
    school_level=alcott['level'],
    focus_group=first_goal['focus_group'],
    focus_area=first_goal['focus_area'],
    outcome=first_goal['outcome'],
    use_ai=False
)
print(f"Result: {result}")
expected = {"focus_grades": first_goal['focus_grades'], "focus_student_group": first_goal['focus_student_group']}
assert result == expected, f"Expected {expected}, got {result}"
print("✓ Test 1 passed\n")

# Test 2: Load from JSON with exact match (use_ai=True, should still use JSON)
print("Test 2: Loading from JSON with use_ai=True (should still use JSON)")
result = normalize_focus_group(
    school_name=alcott['name'],
    school_level=alcott['level'],
    focus_group=first_goal['focus_group'],
    focus_area=first_goal['focus_area'],
    outcome=first_goal['outcome'],
    use_ai=True
)
print(f"Result: {result}")
assert result == expected, f"Expected {expected}, got {result}"
print("✓ Test 2 passed\n")

# Test 3: No match found in JSON with use_ai=False (should return defaults)
print("Test 3: No match in JSON with use_ai=False (should return defaults)")
result = normalize_focus_group(
    school_name="Nonexistent School",
    school_level="Elementary School",
    focus_group="Some random focus group",
    focus_area="Some random area",
    outcome="Some random outcome",
    use_ai=False
)
print(f"Result: {result}")
expected_defaults = {"focus_grades": "All Grades", "focus_student_group": "All Students"}
assert result == expected_defaults, f"Expected {expected_defaults}, got {result}"
print("✓ Test 3 passed\n")

# Test 4: Partial match (same school, different goal) with use_ai=False (should return defaults)
print("Test 4: Partial match (same school, different goal) with use_ai=False")
result = normalize_focus_group(
    school_name="Alcott Elementary",
    school_level="Elementary School",
    focus_group="Different focus group",
    focus_area="Different area",
    outcome="Different outcome",
    use_ai=False
)
print(f"Result: {result}")
assert result == expected_defaults, f"Expected {expected_defaults}, got {result}"
print("✓ Test 4 passed\n")

print("All tests passed! ✓")
