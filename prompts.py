"""
Prompt templates and configurations for genAI queries
"""
import json

def get_action_summary_user_message(school_name: str, outcome: str, strategies: list) -> str:
    """Generate prompt for action summary generation"""
    return f"""
Write a 2-3 sentence paragraph summarizing the actions that {school_name} plans to take in order to achieve the following outcome: "{outcome}". 
The summary should be based on the following actions and associated measures:
{json.dumps(strategies, indent=2)}

Include only the paragraph itself. There should be no headers or other text. If there are multiple actions and measures, weave them together into a single narrative.

If there are no actions or measures given, the paragraph should simply be "Actions not identified. Check SIP document manually."
"""

def get_focus_user_message(school_name: str, school_level: str, focus_group: str, focus_area: str, outcome: str) -> str:
    """Generate prompt for focus group normalization"""
    return f"""
{{ 
    "school_name": "{school_name}",
    "school_level": "{school_level}",
    "focus_group": "{focus_group}",
    "focus_area": "{focus_area}",
    "outcome": "{outcome}"
}}
"""

FOCUS_NORMALIZATION_SYSTEM_PROMPT = f"""
You are normalizing educational focus group/area descriptions for a school improvement plan dashboard. 

Given school name, level, focus group, focus area, and desired outcome, determine the appropriate normalized grade and student group categories.
Use "All Grades" for focus_grades if the focus is on all grades (PK-5 or K-5 for elementary, 6-8 for middle, 9-12 for high) or doesn't specify particular grades.
focus_student_group could be: "Low Income", "ML", "Special Education" (for IEP, 504, or both), "Race/Ethnicity", or "All Students" if the focus is on all students or doesn't specify a particular student group.

The output should be a JSON object with two fields, focus_grades and focus_student_group.

Example #1:
<input>
{get_focus_user_message("Benjamin Franklin Elementary School", "Elementary School", "K-5", 
                        "Family & Staff Opportunities to Participate/Engage the School and Staff Sense of Belonging", 
                        "Increased opportunities for families to provide voice and feedback while also participating in school-based decision-making and governance. Additionally, we will have an explicit focus on increasing sense of belonging amongst our staff members.")}
</input>
<output>
{{
    "focus_grades": "All Grades",
    "focus_student_group": "All Students"
}}
</output>

Example #2:
<input>
{get_focus_user_message("Helen Keller Elementary School", "Elementary School", "K-5", "Elevating Parent Voice of Black Students through Family Engagement", 
                        "By June 2026, 80% of Black/Black-Hispanic/Black two or more races students at Keller will demonstrate growth in social-emotional competencies related to belonging, self-efficacy, and school connectedness, as measured by SEL survey indicators, Panorama SEL data, and behavioral data (office referrals, proactive check-ins, attendance).")}
</input>
<output>
{{
    "focus_grades": "All Grades",
    "focus_student_group": "Race/Ethnicity"
}}
</output>

Example #3:
<input>
{get_focus_user_message("Lakeview Elementary School", "Elementary School", "K-5", "Reading and Literacy", "Close proficiency gap that currently exists between K/1st and 2-5 low-income students as measured by Fastbridge assessment (early reading for K-1 and aReading for 2-5).")}
</input>
<output>
{{
    "focus_grades": "All Grades",
    "focus_student_group": "Low Income"
}}
</output>


Example #4:
<input>
{get_focus_user_message("Horance Mann Elementary School", "Elementary School", "Grades 3 through 5", "Self-regulation and sense of belonging", "Increase in the percent of students who incorporate self-regulation strategies regularly and self-report that they are using these strategies on the Spring 2026 Panorama survey.")}
</input>
<output>
{{
    "focus_grades": "Grades 3-5",
    "focus_student_group": "All Students"
}}
</output>

Example #5:
<input>
{get_focus_user_message("Timberline Middle School", "Middle School", "", "6th - 8th Grade", "")}
</input>
<output>
{{
    "focus_grades": "All Grades",
    "focus_student_group": "All Students"
}}
</output>

Example #6:
<input>
{get_focus_user_message("Explorer Community Elementary School", "Elementary School", "1st", "Phonics and Phonemic Awareness", "By spring 2026, 100% of students will demonstrate growth, or maintain minimal risk, on the FastBridge early reading assessment.")}
</input>
<output>
{{
    "focus_grades": "Grade 1",
    "focus_student_group": "All Students"
}}

Example #7:
<input>
{get_focus_user_message("Kamiakin Middle School", "Middle School", "Subgroup of 8th graders who had a C- or below in 7+ Math last year Subgroup of 6th and 7th graders who received a 1 or a 2 on the SBA last year", "Algebra", "All students meeting standard in Algebra – passing grade in Algebra by 8th grade.")}
</input>
<output>
{{ 
    "focus_grades": "All Grades",
    "focus_student_group": "All Students"
}}
"""