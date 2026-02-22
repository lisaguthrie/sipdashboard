"""
Vector store utilities for semantic search of SIP goals.
Generates embeddings for goals and exports them for use in the dashboard.
"""
import json
import os
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from logger import log_message, INFO, DEBUG, ERROR, WARNING

# Global model instance (loaded once)
_embedding_model = None
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


def init_embedding_model():
    """
    Initialize and load the sentence-transformers model.
    Model is cached globally to avoid reloading.
    
    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model
    
    if _embedding_model is None:
        log_message(INFO, f"Loading embedding model: {MODEL_NAME}")
        try:
            _embedding_model = SentenceTransformer(MODEL_NAME)
            log_message(INFO, f"✓ Model loaded successfully ({EMBEDDING_DIMENSIONS} dimensions)")
        except Exception as e:
            log_message(ERROR, f"Failed to load embedding model: {e}")
            raise
    
    return _embedding_model


def generate_goal_text(goal_dict):
    """
    Generate searchable text from a goal dictionary.
    Concatenates key fields that are most relevant for semantic search.
    
    Args:
        goal_dict: Dictionary containing goal data
        
    Returns:
        String of concatenated goal text
    """
    parts = []
    
    # Priority order: outcome, focus_area, strategies (full text)
    if goal_dict.get('outcome'):
        parts.append(goal_dict['outcome'])
    
    if goal_dict.get('focus_area'):
        parts.append(f"Focus: {goal_dict['focus_area']}")
    
    # Use full strategies text (not summarized)
    strategies = goal_dict.get('strategies', [])
    if strategies and isinstance(strategies, list) and len(strategies) > 0:
        # Format structured strategies
        strategy_texts = []
        for strategy in strategies:
            if isinstance(strategy, dict):
                action = strategy.get('action', '')
                measures = strategy.get('measures', '')
                if action:
                    strategy_texts.append(f"Action: {action}")
                if measures:
                    strategy_texts.append(f"Measures: {measures}")
        if strategy_texts:
            parts.append(" ".join(strategy_texts))
    elif goal_dict.get('raw_strategies'):
        # Fall back to raw strategies text if structured strategies are empty
        parts.append(goal_dict['raw_strategies'])
    else:
        parts.append(goal_dict.get('strategies_summarized', ''))
    
    # Add metadata for better context
    if goal_dict.get('area'):
        parts.append(f"Area: {goal_dict['area']}")
    
    if goal_dict.get('focus_grades'):
        parts.append(f"Grades: {goal_dict['focus_grades']}")
    
    if goal_dict.get('focus_student_group'):
        parts.append(f"Students: {goal_dict['focus_student_group']}")
    
    return " ".join(parts)


def generate_goal_embedding(goal_dict, model=None):
    """
    Generate embedding vector for a single goal.
    
    Args:
        goal_dict: Dictionary containing goal data
        model: Optional pre-loaded model (will load if not provided)
        
    Returns:
        numpy array of embedding vector (384 dimensions)
    """
    if model is None:
        model = init_embedding_model()
    
    text = generate_goal_text(goal_dict)
    embedding = model.encode(text, convert_to_numpy=True)
    
    return embedding


def create_goal_id(school_name, school_level, goal_index, area):
    """
    Create a unique, URL-safe ID for a goal.
    
    Args:
        school_name: Name of the school
        school_level: School level (Elementary/Middle/High)
        goal_index: Index of goal (0, 1, 2)
        area: Goal area (Math, ELA, etc.)
        
    Returns:
        String ID like "juanita-elementary-goal-1-ela"
    """
    # Normalize school name: lowercase, replace spaces/special chars with hyphens
    school_slug = school_name.lower().replace(' ', '-').replace("'", '').replace('.', '')
    level_slug = school_level.lower().replace(' school', '').replace(' ', '-')
    area_slug = area.lower().replace(' ', '-')
    
    return f"{school_slug}-{level_slug}-goal-{goal_index + 1}-{area_slug}"


def build_embeddings_from_json(json_file='schools_extracted.json', output_file='goals_embeddings.json'):
    """
    Read schools JSON and generate embeddings for all goals.
    Exports embeddings as JSON for loading in the dashboard.
    
    Args:
        json_file: Path to schools_extracted.json
        output_file: Path to output embeddings JSON
        
    Returns:
        Path to output file
    """
    log_message(INFO, f"Building embeddings from {json_file}")
    
    # Load schools data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            schools = json.load(f)
        log_message(INFO, f"Loaded {len(schools)} schools")
    except Exception as e:
        log_message(ERROR, f"Failed to load {json_file}: {e}")
        raise
    
    # Initialize embedding model
    model = init_embedding_model()
    
    # Generate embeddings for all goals
    embeddings_data = {
        "model": MODEL_NAME,
        "dimensions": EMBEDDING_DIMENSIONS,
        "goals": []
    }
    
    total_goals = 0
    for school in schools:
        school_name = school.get('name', 'Unknown')
        school_level = school.get('level', 'Unknown')
        goals = school.get('goals', [])
        
        log_message(DEBUG, f"Processing {school_name}: {len(goals)} goals")
        
        for goal_index, goal in enumerate(goals):
            # Generate embedding
            try:
                embedding = generate_goal_embedding(goal, model)
                
                # Create goal entry
                goal_id = create_goal_id(school_name, school_level, goal_index, goal.get('area', 'other'))
                
                strategies = goal.get('strategies', [])
                if not strategies:
                    strategies = goal.get('raw_strategies', 'Not found')

                goal_entry = {
                    "id": goal_id,
                    "school_name": school_name,
                    "school_level": school_level,
                    "goal_index": goal_index,
                    "area": goal.get('area', ''),
                    "focus_grades": goal.get('focus_grades', ''),
                    "focus_student_group": goal.get('focus_student_group', ''),
                    "embedding": embedding.tolist(),  # Convert numpy array to list for JSON
                    "text": f"""
School name: {school_name} ({school_level})
Goal #{goal_index + 1} ({goal.get('area', 'Other')}, {goal.get('focus_grades', 'Unknown Focus Grades')}, {goal.get('focus_student_group', 'Unknown Focus Student Group')}): {goal.get('outcome', 'Outcome not found')}
Focus Area: {goal.get('focus_area', 'Not found')}
Current Data: {goal.get('currentdata', 'Not found')}
Strategies: {strategies}
Engagement Strategies: {goal.get('engagement_strategies', 'Not found')}
"""
                }
                
                embeddings_data['goals'].append(goal_entry)
                total_goals += 1
                
            except Exception as e:
                log_message(WARNING, f"Failed to generate embedding for {school_name} goal {goal_index + 1}: {e}")
                continue
    
    # Write embeddings to JSON
    log_message(INFO, f"Generated {total_goals} embeddings, writing to {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2, ensure_ascii=False)
        
        # Check file size
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        log_message(INFO, f"✓ Embeddings saved: {output_file} ({file_size:.2f} MB)")
        
    except Exception as e:
        log_message(ERROR, f"Failed to write {output_file}: {e}")
        raise
    
    return output_file


def cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector (numpy array or list)
        vec2: Second vector (numpy array or list)
        
    Returns:
        Float similarity score between -1 and 1 (higher = more similar)
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def search_goals(query, embeddings_file='goals_embeddings.json', top_k=10, filters=None):
    """
    Search for goals semantically similar to a query.
    
    Args:
        query: Search query string
        embeddings_file: Path to embeddings JSON file
        top_k: Number of results to return
        filters: Optional dict of filters (area, school_level, focus_grades, focus_student_group)
        
    Returns:
        List of goal entries sorted by similarity score
    """
    # Load embeddings
    try:
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
    except Exception as e:
        log_message(ERROR, f"Failed to load embeddings: {e}")
        return []
    
    # Generate query embedding
    model = init_embedding_model()
    query_embedding = model.encode(query, convert_to_numpy=True)
    
    # Compute similarities
    results = []
    for goal in embeddings_data['goals']:
        # Apply filters if provided
        if filters:
            if filters.get('area') and goal['area'] != filters['area']:
                continue
            if filters.get('school_level') and goal['school_level'] != filters['school_level']:
                continue
            if filters.get('focus_grades') and goal['focus_grades'] != filters['focus_grades']:
                continue
            if filters.get('focus_student_group') and goal['focus_student_group'] != filters['focus_student_group']:
                continue
        
        # Compute similarity
        goal_embedding = np.array(goal['embedding'])
        similarity = cosine_similarity(query_embedding, goal_embedding)
        
        results.append({
            **goal,
            'similarity': float(similarity)
        })
    
    # Sort by similarity (highest first) and return top_k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    # Quick test/demo
    import sys
    
    if len(sys.argv) > 1:
        # Test search with command-line query
        query = ' '.join(sys.argv[1:])
        log_message(INFO, f"Searching for: '{query}'")
        
        results = search_goals(query, top_k=5)
        
        print(f"\nTop {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['school_name']} - {result['area']}")
            print(f"   Similarity: {result['similarity']:.3f}")
            print(f"   Outcome: {result['content']['outcome'][:100]}...")
    else:
        # Build embeddings from schools_extracted.json
        build_embeddings_from_json()
