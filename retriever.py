"""Assessment retrieval with multiple search strategies."""
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from utils import load_assessment_data, normalize_assessment, calculate_similarity, extract_keywords


class AssessmentRetriever:
    """Handles all assessment search and retrieval operations."""
    
    def __init__(self, catalog_path: str = "shl_catalog_master.json"):
        """
        Initialize retriever with catalog data.
        
        Args:
            catalog_path: Path to SHL catalog JSON file
        """
        self.catalog_path = catalog_path
        self.assessments: List[Dict[str, Any]] = []
        self._load_data()
    
    def _load_data(self) -> None:
        """Load and normalize assessment data."""
        raw_data = load_assessment_data(self.catalog_path)
        self.assessments = [normalize_assessment(item) for item in raw_data]
        print(f"✅ Loaded {len(self.assessments)} assessments from {self.catalog_path}")
    
    def search_by_keyword(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search assessments by keyword matching.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching assessments
        """
        if not self.assessments:
            return []
        
        query_lower = query.lower()
        query_keywords = extract_keywords(query)
        scored = []
        
        for assessment in self.assessments:
            score = 0
            search_text = f"{assessment['name']} {assessment['description']} {' '.join(assessment['keys'])} {' '.join(assessment['job_levels'])}".lower()
            
            # Exact phrase match
            if query_lower in assessment['name'].lower():
                score += 20
            
            # Keyword matches
            for keyword in query_keywords:
                if keyword in search_text:
                    score += 2
                if keyword in assessment['name'].lower():
                    score += 5
            
            # Job level match
            for level in assessment['job_levels']:
                if level.lower() in query_lower:
                    score += 3
            
            # Key/category match
            for key in assessment['keys']:
                if key.lower() in query_lower:
                    score += 4
            
            if score > 0:
                scored.append((score, assessment))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [assess for _, assess in scored[:limit]]
    
    def search_by_semantic(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple semantic search using keyword importance.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching assessments
        """
        # Fallback to keyword search since we're not using external APIs
        return self.search_by_keyword(query, limit)
    
    def find_exact_match(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Find exact match by name or ID.
        
        Args:
            query: Search query
            
        Returns:
            Assessment if found, None otherwise
        """
        query_lower = query.lower().strip()
        
        for assessment in self.assessments:
            if assessment['name'].lower() == query_lower:
                return assessment
            if query_lower in assessment['name'].lower():
                return assessment
            if assessment['id'] == query:
                return assessment
        
        return None
    
    def find_similar(self, query: str, threshold: float = 0.3, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar assessments using name similarity.
        
        Args:
            query: Search query
            threshold: Minimum similarity score
            limit: Maximum results
            
        Returns:
            List of similar assessments
        """
        if not self.assessments:
            return []
        
        scored = []
        for assessment in self.assessments:
            similarity = calculate_similarity(query, assessment['name'])
            if similarity >= threshold:
                scored.append((similarity, assessment))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [assess for _, assess in scored[:limit]]
    
    def get_recommendations(self, query: str, max_results: int = 5) -> Tuple[List[Dict[str, Any]], str]:
        """
        Get recommendations based on query.
        
        Args:
            query: User query
            max_results: Maximum number of recommendations
            
        Returns:
            Tuple of (recommendations, status_message)
        """
        if not self.assessments:
            return [], "No assessment data available."
        
        # Try exact match first
        exact = self.find_exact_match(query)
        if exact:
            return [exact], "Found matching assessment in SHL catalog."
        
        # Try keyword search
        keyword_results = self.search_by_keyword(query, max_results)
        if keyword_results:
            return keyword_results, f"Found {len(keyword_results)} relevant assessments."
        
        # Try similar names
        similar = self.find_similar(query, threshold=0.3, limit=max_results)
        if similar:
            return similar, "No exact match found. Here are similar assessments from the SHL catalog:"
        
        # No results
        available = [a['name'] for a in self.assessments[:5]]
        return [], f"No matches found. Available assessments: {', '.join(available)}"
    
    def compare_assessments(self, name1: str, name2: str) -> Dict[str, Any]:
        """
        Compare two assessments.
        
        Args:
            name1: First assessment name
            name2: Second assessment name
            
        Returns:
            Comparison dictionary
        """
        assess1 = self.find_exact_match(name1)
        assess2 = self.find_exact_match(name2)
        
        if not assess1:
            return {'error': f"Could not find '{name1}' in catalog"}
        if not assess2:
            return {'error': f"Could not find '{name2}' in catalog"}
        
        return {
            'assessment1': assess1,
            'assessment2': assess2,
            'comparison': {
                'name': [assess1['name'], assess2['name']],
                'type': [assess1['test_type'], assess2['test_type']],
                'duration': [assess1['duration'], assess2['duration']],
                'remote': [assess1['remote_testing'], assess2['remote_testing']],
                'adaptive': [assess1['adaptive_support'], assess2['adaptive_support']],
                'job_levels': [assess1['job_levels'][:3], assess2['job_levels'][:3]]
            }
        }
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all assessments."""
        return self.assessments
    
    def count(self) -> int:
        """Get number of assessments."""
        return len(self.assessments)