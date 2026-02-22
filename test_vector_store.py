"""
Tests for vector_store.py functionality.
Run with: pytest test_vector_store.py -v
"""
import pytest
import json
import os
import numpy as np
from pathlib import Path
from vector_store import (
    init_embedding_model,
    generate_goal_text,
    generate_goal_embedding,
    create_goal_id,
    build_embeddings_from_json,
    cosine_similarity,
    search_goals,
    MODEL_NAME,
    EMBEDDING_DIMENSIONS
)


@pytest.fixture
def sample_goal():
    """Sample goal for testing"""
    return {
        "area": "Math",
        "focus_group": "Grades 6-8",
        "focus_area": "Algebra readiness",
        "focus_grades": "Grades 6-8",
        "focus_student_group": "All Students",
        "outcome": "By Spring 2026, 75% of students will demonstrate proficiency in algebraic thinking.",
        "currentdata": "Currently 60% of students meet standards.",
        "school_name": "Test Middle School",
        "strategies": [
            {"action": "Implement daily problem solving", "measures": "Weekly assessments"}
        ],
        "strategies_summarized": "Students will engage in daily algebraic problem-solving activities with weekly progress monitoring.",
        "engagement_strategies": "Parent workshops on supporting math at home."
    }


@pytest.fixture
def schools_json_file(tmp_path):
    """Create temporary schools_extracted.json for testing"""
    schools_data = [
        {
            "name": "Test Elementary School",
            "level": "Elementary School",
            "goals": [
                {
                    "area": "ELA",
                    "focus_group": "Grades K-2",
                    "focus_area": "Reading fluency",
                    "focus_grades": "Grades K-2",
                    "focus_student_group": "All Students",
                    "outcome": "80% of K-2 students will read at grade level by Spring 2026.",
                    "currentdata": "Current reading levels vary.",
                    "school_name": "Test Elementary School",
                    "strategies": [],
                    "strategies_summarized": "Implement daily guided reading with phonics instruction.",
                    "engagement_strategies": "Family literacy nights."
                },
                {
                    "area": "Math",
                    "focus_group": "Grade 3",
                    "focus_area": "Multiplication facts",
                    "focus_grades": "Grade 3",
                    "focus_student_group": "All Students",
                    "outcome": "All 3rd graders will master multiplication facts by June 2026.",
                    "currentdata": "50% currently proficient.",
                    "school_name": "Test Elementary School",
                    "strategies": [],
                    "strategies_summarized": "Daily fact practice with gamification and timed assessments.",
                    "engagement_strategies": "Math homework support."
                }
            ]
        },
        {
            "name": "Test High School",
            "level": "High School",
            "goals": [
                {
                    "area": "Graduation",
                    "focus_group": "Grade 12",
                    "focus_area": "On-time graduation",
                    "focus_grades": "Grade 12",
                    "focus_student_group": "All Students",
                    "outcome": "95% graduation rate by June 2026.",
                    "currentdata": "Current rate is 88%.",
                    "school_name": "Test High School",
                    "strategies": [],
                    "strategies_summarized": "Credit recovery programs and mentorship for at-risk students.",
                    "engagement_strategies": "Senior support meetings."
                }
            ]
        }
    ]
    
    json_file = tmp_path / "schools_test.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(schools_data, f, indent=2, ensure_ascii=False)
    
    return str(json_file)


def test_init_embedding_model():
    """Test that the embedding model loads successfully"""
    model = init_embedding_model()
    assert model is not None
    assert hasattr(model, 'encode')


def test_generate_goal_text(sample_goal):
    """Test goal text generation"""
    text = generate_goal_text(sample_goal)
    
    # Check that key fields are included
    assert 'algebraic thinking' in text.lower()
    assert 'algebra readiness' in text.lower()
    assert 'math' in text.lower()
    assert 'grades 6-8' in text.lower()
    
    # Verify full strategies text is included (not summarized)
    assert 'implement daily problem solving' in text.lower()
    assert 'weekly assessments' in text.lower()
    
    # Verify summarized version is NOT used for embedding text
    assert 'daily algebraic problem-solving activities' not in text.lower()


def test_generate_goal_text_with_raw_strategies():
    """Test goal text generation falls back to raw_strategies when strategies list is empty"""
    goal_with_raw = {
        "area": "ELA",
        "outcome": "Improve reading scores",
        "focus_area": "Literacy",
        "strategies": [],  # Empty strategies list
        "raw_strategies": "Teachers will implement guided reading sessions with differentiated instruction.",
        "focus_grades": "All Grades",
        "focus_student_group": "All Students"
    }
    
    text = generate_goal_text(goal_with_raw)
    
    # Verify raw_strategies text is included as fallback
    assert 'guided reading sessions' in text.lower()
    assert 'differentiated instruction' in text.lower()


def test_generate_goal_embedding(sample_goal):
    """Test embedding generation for a single goal"""
    embedding = generate_goal_embedding(sample_goal)
    
    # Check embedding properties
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (EMBEDDING_DIMENSIONS,)
    assert not np.isnan(embedding).any()
    assert not np.isinf(embedding).any()


def test_create_goal_id():
    """Test goal ID creation"""
    goal_id = create_goal_id("Test Middle School", "Middle School", 0, "Math")
    
    assert isinstance(goal_id, str)
    assert 'test-middle-school' in goal_id
    assert 'middle' in goal_id
    assert 'goal-1' in goal_id
    assert 'math' in goal_id
    
    # Test with special characters
    goal_id2 = create_goal_id("St. Mary's School", "Elementary School", 2, "9th Grade Success")
    assert "st-marys" in goal_id2
    assert "goal-3" in goal_id2


def test_cosine_similarity():
    """Test cosine similarity calculation"""
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([1.0, 0.0, 0.0])
    vec3 = np.array([0.0, 1.0, 0.0])
    vec4 = np.array([-1.0, 0.0, 0.0])
    
    # Identical vectors should have similarity 1.0
    assert abs(cosine_similarity(vec1, vec2) - 1.0) < 0.001
    
    # Orthogonal vectors should have similarity 0.0
    assert abs(cosine_similarity(vec1, vec3)) < 0.001
    
    # Opposite vectors should have similarity -1.0
    assert abs(cosine_similarity(vec1, vec4) - (-1.0)) < 0.001


def test_build_embeddings_from_json(schools_json_file, tmp_path):
    """Test building embeddings from a schools JSON file"""
    output_file = tmp_path / "embeddings_test.json"
    
    result_file = build_embeddings_from_json(
        json_file=schools_json_file,
        output_file=str(output_file)
    )
    
    # Check that file was created
    assert os.path.exists(result_file)
    
    # Load and validate embeddings
    with open(result_file, 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)
    
    # Check structure
    assert 'model' in embeddings_data
    assert embeddings_data['model'] == MODEL_NAME
    assert 'dimensions' in embeddings_data
    assert embeddings_data['dimensions'] == EMBEDDING_DIMENSIONS
    assert 'goals' in embeddings_data
    
    # Should have 3 goals (2 from elementary + 1 from high school)
    goals = embeddings_data['goals']
    assert len(goals) == 3
    
    # Check first goal structure
    goal = goals[0]
    assert 'id' in goal
    assert 'school_name' in goal
    assert 'school_level' in goal
    assert 'goal_index' in goal
    assert 'area' in goal
    assert 'embedding' in goal
    assert 'content' in goal
    
    # Check embedding is correct length
    assert len(goal['embedding']) == EMBEDDING_DIMENSIONS
    
    # Check content fields
    content = goal['content']
    assert 'outcome' in content
    assert 'focus_area' in content
    assert 'strategies_summarized' in content


def test_search_goals(schools_json_file, tmp_path):
    """Test semantic search functionality"""
    # First build embeddings
    embeddings_file = tmp_path / "embeddings_test.json"
    build_embeddings_from_json(
        json_file=schools_json_file,
        output_file=str(embeddings_file)
    )
    
    # Test search queries
    results = search_goals("reading and literacy", embeddings_file=str(embeddings_file), top_k=3)
    
    # Should return results
    assert len(results) > 0
    assert len(results) <= 3
    
    # Results should have similarity scores
    assert 'similarity' in results[0]
    assert isinstance(results[0]['similarity'], float)
    
    # Results should be sorted by similarity (descending)
    if len(results) > 1:
        assert results[0]['similarity'] >= results[1]['similarity']
    
    # Top result should be the ELA reading goal
    assert results[0]['area'] == 'ELA'
    assert 'reading' in results[0]['content']['focus_area'].lower()


def test_search_with_filters(schools_json_file, tmp_path):
    """Test search with metadata filters"""
    # Build embeddings
    embeddings_file = tmp_path / "embeddings_test.json"
    build_embeddings_from_json(
        json_file=schools_json_file,
        output_file=str(embeddings_file)
    )
    
    # Search with area filter
    results = search_goals(
        "student success",
        embeddings_file=str(embeddings_file),
        top_k=10,
        filters={'area': 'Math'}
    )
    
    # Should only return Math goals
    assert len(results) > 0
    for result in results:
        assert result['area'] == 'Math'
    
    # Search with level filter
    results = search_goals(
        "graduation",
        embeddings_file=str(embeddings_file),
        top_k=10,
        filters={'school_level': 'High School'}
    )
    
    # Should only return high school goals
    assert len(results) > 0
    for result in results:
        assert result['school_level'] == 'High School'


def test_semantic_relevance():
    """Test that semantically related queries return relevant results"""
    # This test requires the actual schools_extracted.json file
    if not os.path.exists('schools_extracted.json'):
        pytest.skip("schools_extracted.json not found")
    
    if not os.path.exists('goals_embeddings.json'):
        # Build embeddings if they don't exist
        build_embeddings_from_json()
    
    # Test various semantic queries
    test_queries = [
        ("third grade math interventions", "Math"),
        ("literacy and reading programs", "ELA"),
        ("social emotional learning", "SEL"),
        ("graduation rates", "Graduation"),
    ]
    
    for query, expected_area in test_queries:
        results = search_goals(query, top_k=5)
        
        # At least one of the top results should match the expected area
        top_areas = [r['area'] for r in results[:3]]
        assert expected_area in top_areas, f"Query '{query}' didn't return {expected_area} in top 3"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])
