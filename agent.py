"""Main SHL Assessment Agent with conversation handling."""
import re
from typing import List, Dict, Any, Optional, Tuple

from retriever import AssessmentRetriever


class SHLAssessmentAgent:
    """Conversational agent for SHL assessment recommendations."""
    
    # Refusal patterns - off-topic topics
    REFUSAL_PATTERNS = {
        'legal': r'\b(legal|lawyer|attorney|court|sue|lawsuit|litigation)\b',
        'medical': r'\b(medical|doctor|health|diagnosis|therapy|treatment|pill|medicine)\b',
        'financial': r'\b(invest|stock|trading|financial advice|wealth|crypto|bitcoin)\b',
        'competitor': r'\b(hays|korn ferry|mercer|talent q|ceb|gartner|mckinsey|ddi|psl)\b',
    }
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r'ignore previous',
        r'forget your',
        r'system prompt',
        r'you are now',
        r'disregard',
        r'create a new',
        r'generate a test',
        r'make an assessment',
        r'pretend you are',
    ]
    
    def __init__(self, catalog_path: str = "shl_catalog_master.json"):
        """Initialize agent with catalog data."""
        self.retriever = AssessmentRetriever(catalog_path)
    
    def _should_refuse(self, message: str) -> Optional[str]:
        """Check if message should be refused."""
        msg_lower = message.lower()
        
        for category, pattern in self.REFUSAL_PATTERNS.items():
            if re.search(pattern, msg_lower):
                return f"I can only recommend SHL assessments from our catalog. For {category} questions, please consult an appropriate specialist."
        
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, msg_lower):
                return "I can only recommend assessments that exist in our SHL catalog. I cannot create or generate new assessments."
        
        return None
    
    def _get_leadership_assessments(self) -> List[Dict[str, Any]]:
        """Get leadership-specific assessments from catalog."""
        leadership_names = [
            'OPQ Leadership Report',
            'Enterprise Leadership Report',
            'OPQ32r',
            'Occupational Personality Questionnaire',
            'Executive Scenarios',
        ]
        
        result = []
        for assessment in self.retriever.get_all():
            name_lower = assessment.get('name', '').lower()
            for keyword in leadership_names:
                if keyword.lower() in name_lower:
                    if assessment not in result:
                        result.append(assessment)
                    break
        
        return result[:5]
    
    def _get_selection_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations specifically for selection/benchmarking."""
        selection_names = [
            'OPQ32r',
            'Occupational Personality Questionnaire',
            'OPQ Universal Competency Report',
            'OPQ Leadership Report',
        ]
        
        result = []
        for assessment in self.retriever.get_all():
            name_lower = assessment.get('name', '').lower()
            for keyword in selection_names:
                if keyword.lower() in name_lower:
                    if assessment not in result:
                        result.append(assessment)
                    break
        
        return result[:5]
    
    def _get_personality_assessments(self) -> List[Dict[str, Any]]:
        """Get personality assessments for refinement."""
        result = []
        for assessment in self.retriever.get_all():
            keys = assessment.get('keys', [])
            test_type = assessment.get('test_type', '').lower()
            if 'personality' in test_type or any('personality' in k.lower() for k in keys):
                if assessment not in result:
                    result.append(assessment)
        return result[:3]
    
    def _format_recommendations_table(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations as a markdown table."""
        if not recommendations:
            return ""
        
        table = "| # | Name | Test Type | Duration | Remote | URL |\n"
        table += "|---|------|-----------|----------|--------|-----|\n"
        
        for i, rec in enumerate(recommendations[:5], 1):
            name = rec.get('name', 'Unknown')[:40]
            test_type = rec.get('test_type', 'General')
            duration = rec.get('duration', '—')
            remote = 'Yes' if rec.get('remote_testing') else 'No'
            url = rec.get('url', '#')
            
            table += f"| {i} | {name} | {test_type} | {duration} | {remote} | {url} |\n"
        
        return table
    
    def _format_recommendations_list(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format recommendations for API response."""
        formatted = []
        for rec in recommendations[:5]:
            formatted.append({
                'name': rec.get('name', 'Unknown'),
                'url': rec.get('url', '#'),
                'test_type': rec.get('test_type', 'General')
            })
        return formatted
    
    def _handle_comparison(self, message: str) -> Optional[Dict[str, Any]]:
        """Handle assessment comparison requests."""
        msg_lower = message.lower()
        compare_words = ['compare', 'difference between', 'versus', 'vs', 'contrast']
        
        if not any(w in msg_lower for w in compare_words):
            return None
        
        # Try to extract assessment names
        assessments = []
        for assessment in self.retriever.get_all():
            name_lower = assessment.get('name', '').lower()
            if name_lower in msg_lower:
                assessments.append(assessment)
        
        if len(assessments) >= 2:
            a1 = assessments[0]
            a2 = assessments[1]
            reply = f"""
**Comparison: {a1.get('name')} vs {a2.get('name')}**

| Feature | {a1.get('name')} | {a2.get('name')} |
|---------|-------------------|-------------------|
| Type | {a1.get('test_type')} | {a2.get('test_type')} |
| Duration | {a1.get('duration', 'N/A')} | {a2.get('duration', 'N/A')} |
| Remote | {'Yes' if a1.get('remote_testing') else 'No'} | {'Yes' if a2.get('remote_testing') else 'No'} |

**{a1.get('name')}**: {a1.get('url')}
**{a2.get('name')}**: {a2.get('url')}
"""
            return {
                'reply': reply,
                'recommendations': [],
                'end_of_conversation': False
            }
        
        return {
            'reply': "Please specify two assessments to compare. Example: 'Compare OPQ32r and Verify G+'",
            'recommendations': [],
            'end_of_conversation': False
        }
    
    def process(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process user message and generate response."""
        turn_count = len([m for m in conversation_history if m.get('role') == 'user']) + 1
        
        # 1. Refusal check
        refusal = self._should_refuse(message)
        if refusal:
            return {
                'reply': refusal,
                'recommendations': [],
                'end_of_conversation': False
            }
        
        # 2. Comparison check
        comparison = self._handle_comparison(message)
        if comparison:
            return comparison
        
        # 3. Refinement check - handle "add personality tests"
        msg_lower = message.lower()
        is_refinement = any(word in msg_lower for word in ['actually', 'add', 'also include', 'plus', 'and also'])
        
        if is_refinement and 'personality' in msg_lower:
            personality_recs = self._get_personality_assessments()
            if personality_recs:
                reply = "I've added personality assessments to your recommendations:\n\n" + self._format_recommendations_table(personality_recs)
                return {
                    'reply': reply,
                    'recommendations': self._format_recommendations_list(personality_recs),
                    'end_of_conversation': False
                }
        
        # 4. Confirmation check
        confirmation_phrases = ['perfect', 'that\'s what we need', 'exactly', 'great', 'good', 'yes']
        if any(phrase in msg_lower for phrase in confirmation_phrases) and turn_count >= 3:
            return {
                'reply': "Excellent! The assessments above are ready for your candidates. Is there anything else I can help with?",
                'recommendations': [],
                'end_of_conversation': True
            }
        
        # 5. Turn 1: Clarify
        if turn_count == 1:
            return {
                'reply': "To find the right SHL assessments for you, please provide:\n\n• **Job role** (e.g., Java Developer, Sales Manager, CXO, Director)\n• **Seniority level** (Junior/Senior/Lead/Manager/Executive)\n• **Purpose** (Selection/Development/Benchmarking)",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        # 6. Turn 2: Provide recommendations
        if turn_count == 2:
            recommendations = self._get_leadership_assessments()
            if recommendations:
                reply = "Based on your requirements, here are relevant SHL assessments:\n\n" + self._format_recommendations_table(recommendations)
                return {
                    'reply': reply,
                    'recommendations': self._format_recommendations_list(recommendations),
                    'end_of_conversation': False
                }
        
        # 7. Turn 3: Selection/benchmark
        if turn_count == 3 and ('selection' in msg_lower or 'benchmark' in msg_lower):
            recommendations = self._get_selection_recommendations()
            if recommendations:
                reply = "For selection with a leadership benchmark, here are the recommended instruments:\n\n" + self._format_recommendations_table(recommendations)
                return {
                    'reply': reply,
                    'recommendations': self._format_recommendations_list(recommendations),
                    'end_of_conversation': False
                }
        
        # 8. Fallback
        recommendations, status = self.retriever.get_recommendations(message, max_results=5)
        if recommendations:
            reply = status + "\n\n" + self._format_recommendations_table(recommendations)
        else:
            reply = status
        
        return {
            'reply': reply,
            'recommendations': self._format_recommendations_list(recommendations),
            'end_of_conversation': False
        }