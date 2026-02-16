"""
Tests for AI helper functions
"""
import unittest
import json
from unittest.mock import Mock, patch
from ai_helper import normalize_focus_group, set_client

class TestFocusGroupNormalization(unittest.TestCase):
    
    def setUp(self):
        """Set up mock AI client"""
        self.mock_client = Mock()
        set_client(self.mock_client)
    
    def test_ai_disabled(self):
        """Test that All Grades/All Students is returned when AI is disabled"""
        result = normalize_focus_group("Northstar Middle School", "Middle School", "6th Grade", "Multilingual learners", "Increase ELA SBA scores for 6th graders identified for multilingual learner supports", use_ai=False)
        
        self.assertEqual(json.dumps(result), json.dumps({"focus_grades": "All Grades", "focus_student_group": "All Students"}))
        self.mock_client.messages.create.assert_not_called()

if __name__ == "__main__":
    unittest.main()