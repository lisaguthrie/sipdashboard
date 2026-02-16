"""
AI helper functions for data normalization
"""
from dotenv import load_dotenv
import os
import json
from anthropic import Anthropic
from anthropic.types import TextBlock
from prompts import FOCUS_NORMALIZATION_SYSTEM_PROMPT, get_focus_user_message, get_action_summary_user_message
from logger import *

SIMPLE_MODEL = "claude-haiku-4-5-20251001"  # For testing/debugging - faster and cheaper than sonnet, but less accurate

# Initialize client (can be mocked for testing)
_client = None

# Load environment variables from .env file
load_dotenv()

def get_client():
    """Get or create Anthropic client"""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        _client = Anthropic(api_key=api_key)
    return _client

def _load_focus_from_json(school_name: str, focus_group: str, focus_area: str, outcome: str) -> dict | None:
    """
    Attempt to load focus_grades and focus_student_group from schools_extracted.json
    by matching school name and all three goal parameters.
    
    Args:
        school_name: Name of the school
        focus_group: Raw focus group description from SIP
        focus_area: Focus area for the goal
        outcome: Desired outcome for the goal
    
    Returns:
        Dictionary with focus_grades and focus_student_group if found, None otherwise
    """
    try:
        # Load schools_extracted.json from the same directory as this script
        json_path = os.path.join(os.path.dirname(__file__), 'schools_extracted.json')
        
        if not os.path.exists(json_path):
            log_message(DEBUG, f"schools_extracted.json not found at {json_path}")
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            schools = json.load(f)
        
        # Search for matching school (case-insensitive)
        school_name_lower = school_name.lower().strip()
        matching_school = None
        
        for school in schools:
            if school.get('name', '').lower().strip() == school_name_lower:
                matching_school = school
                break
        
        if not matching_school:
            log_message(DEBUG, f"School '{school_name}' not found in schools_extracted.json")
            return None
        
        # Search for matching goal by comparing all three parameters
        focus_group_lower = focus_group.lower().strip()
        focus_area_lower = focus_area.lower().strip()
        outcome_lower = outcome.lower().strip()
        
        for goal in matching_school.get('goals', []):
            goal_focus_group = goal.get('focus_group', '').lower().strip()
            goal_focus_area = goal.get('focus_area', '').lower().strip()
            goal_outcome = goal.get('outcome', '').lower().strip()
            
            # All three fields must match
            if (goal_focus_group == focus_group_lower and 
                goal_focus_area == focus_area_lower and 
                goal_outcome == outcome_lower):
                
                result = {
                    'focus_grades': goal.get('focus_grades', 'All Grades'),
                    'focus_student_group': goal.get('focus_student_group', 'All Students')
                }
                log_message(DEBUG, f"Loaded focus data from JSON for '{school_name}': {result}")
                return result
        
        log_message(DEBUG, f"No matching goal found in schools_extracted.json for '{school_name}'")
        return None
        
    except json.JSONDecodeError as e:
        log_message(DEBUG, f"Failed to parse schools_extracted.json: {e}")
        return None
    except Exception as e:
        log_message(DEBUG, f"Error loading from schools_extracted.json: {e}")
        return None

def normalize_focus_group(school_name: str, school_level: str, focus_group: str, focus_area: str, outcome: str,use_ai: bool = True) -> dict:
    """
    Identify/normalize the target grade(s) and student groups for a given SIP goal, using an AI model to interpret the raw descriptions.
    
    Args:
        school_name: Name of the school (for context)
        school_level: School level (Elementary School, Middle School, High School)
        focus_group: Raw focus group description from SIP
        focus_area: Focus area for the goal
        outcome: Desired outcome for the goal
        use_ai: If False, returns All Grades/All Students (for testing)
    
    Returns:
        Dictionary with keys 'focus_grades' (All Grades, or specific grade range) and 'focus_student_group' (All Students, or Low Income, ML, Special Education, Race/Ethnicity)
    """
    # Always try to load from schools_extracted.json first
    cached_result = _load_focus_from_json(school_name, focus_group, focus_area, outcome)
    if cached_result is not None:
        log_message(INFO, f"Loaded focus data for '{school_name}' from JSON cache.")
        return cached_result
    
    # If JSON lookup failed and use_ai is False, return defaults
    if not use_ai:
        return {
            "focus_grades": "All Grades",
            "focus_student_group": "All Students"
        }
    
    # If JSON lookup failed and use_ai is True, call Claude API
    try:
        client = get_client()
        user_message = get_focus_user_message(school_name, school_level, focus_group, focus_area, outcome)
        
        message = client.messages.create(
            model=SIMPLE_MODEL,
            max_tokens=100,
            stop_sequences=["```"],
            # Use prompt caching for the system prompt
            system=[
                {
                    "type": "text",
                    "text": FOCUS_NORMALIZATION_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}  # Mark for caching
                }
            ],
            messages=[
                {"role": "user", "content": user_message},
                { "role": "assistant", "content": "```json" } # ensure model outputs JSON without extra text by starting with a code block
            ]
        )
        
        # Extract text from the first TextBlock in the content
        normalized = None
        for block in message.content:
            if isinstance(block, TextBlock):
                normalized = block.text.strip()
                break
        
        if normalized is None:
            raise ValueError("No text content in response")
        
        # Log cache performance
        usage = message.usage
        if hasattr(usage, 'cache_creation_input_tokens') and usage.cache_creation_input_tokens is not None and usage.cache_creation_input_tokens > 0:
            log_message(DEBUG, f"   Cache created: {usage.cache_creation_input_tokens} tokens")
        if hasattr(usage, 'cache_read_input_tokens') and usage.cache_read_input_tokens is not None and usage.cache_read_input_tokens > 0:
            log_message(DEBUG, f"   Cache hit: {usage.cache_read_input_tokens} tokens")
        
        # Parse normalized (which is a JSON string) into dictionary
        result = json.loads(normalized)
        return result
        
    except Exception as e:
        # Fallback to original on error
        log_message(WARNING, f"AI normalization failed for '{focus_group}': {e}")
        return {
            "focus_grades": "All Grades",
            "focus_student_group": "All Students"
        }

def get_actions_summary(school_name: str, outcome: str, strategies: list, use_ai: bool = True) -> str:
    """Generate action summary using AI model"""
    if not use_ai:
        return "Summary not available (AI disabled for testing)."

    try:
        client = get_client()
        user_message = get_action_summary_user_message(school_name, outcome, strategies)
        
        message = client.messages.create(
            model=SIMPLE_MODEL,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # Extract text from the first TextBlock in the content
        summary = None
        for block in message.content:
            if isinstance(block, TextBlock):
                summary = block.text.strip()
                break
        
        if summary is None:
            raise ValueError("No text content in response")
        
        return summary
        
    except Exception as e:
        log_message(WARNING, f"AI action summary generation failed for '{school_name}': {e}")
        return "Summary not available due to an error."

# For testing - inject a mock client
def set_client(client):
    """Set custom client (for testing)"""
    global _client
    _client = client