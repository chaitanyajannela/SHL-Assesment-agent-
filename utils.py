"""Utility functions for data loading and processing."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


def load_assessment_data(file_path: str = "shl_catalog_master.json") -> List[Dict[str, Any]]:
    """
    Load assessment data from JSON file.
    
    Args:
        file_path: Path to the JSON catalog file
        
    Returns:
        List of assessment dictionaries
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Catalog file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError(f"Unexpected data format in {file_path}")
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def normalize_assessment(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize assessment data for consistent access.
    
    Args:
        raw: Raw assessment dictionary from JSON
        
    Returns:
        Normalized assessment dictionary
    """
    return {
        'id': str(raw.get('entity_id', '')),
        'name': raw.get('name', 'Unknown'),
        'url': raw.get('link', ''),
        'test_type': raw.get('keys', ['Assessment'])[0] if raw.get('keys') else 'Assessment',
        'description': raw.get('description', ''),
        'job_levels': raw.get('job_levels', []),
        'languages': raw.get('languages', []),
        'duration': raw.get('duration', 'Not specified'),
        'remote_testing': raw.get('remote', 'no') == 'yes',
        'adaptive_support': raw.get('adaptive', 'no') == 'yes',
        'keys': raw.get('keys', []),
        'raw_data': raw
    }


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate string similarity ratio."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    stop_words = {'i', 'need', 'want', 'for', 'a', 'an', 'the', 'to', 'of', 'and', 'in', 'on', 'at', 'with', 'is', 'are', 'am', 'be', 'by'}
    import re
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    return [w for w in words if w not in stop_words]