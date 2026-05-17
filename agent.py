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
        r'act as if',
        r'override',
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
        leadership_assessments = []
        leadership_keywords = [
            'OPQ Leadership Report',
            'Enterprise Leadership Report',
            'OPQ32r',
            'Occupational Personality Questionnaire',
            'OPQ Universal Competency Report',
            'Executive Scenarios',
            'Virtual Assessment and Development Centers',
            'MFS 360 Enterprise Leadership Report'
        ]
        
        for assessment in self.retriever.get_all():
            name_lower = assessment.get('name', '').lower()
            for keyword in leadership_keywords:
                if keyword.lower() in name_lower:
                    if assessment not in leadership_assessments:
                        leadership_assessments.append(assessment)
                        break
        
        return leadership_assessments[:5]
    
    def _get_selection_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations specifically for selection/benchmarking."""
        selection_assessments = []
        selection_keywords = [
            'OPQ Leadership Report',
            'OPQ32r',
            'Occupational Personality Questionnaire',
            'Enterprise Leadership Report',
            'OPQ Universal Competency Report',
            'Selection Report'
        ]
        
        for assessment in self.retriever.get_all():
            name_lower = assessment.get('name', '').lower()
            for keyword in selection_keywords:
                if keyword.lower() in name_lower:
                    if assessment not in selection_assessments:
                        selection_assessments.append(assessment)
                        break
        
        # Order matters - put OPQ32r first
        ordered = []
        for name in ['OPQ32r', 'Occupational Personality Questionnaire', 'OPQ Universal Competency Report', 'OPQ Leadership Report', 'Enterprise Leadership Report']:
            for a in selection_assessments:
                if name.lower() in a.get('name', '').lower() and a not in ordered:
                    ordered.append(a)
                    break
        
        return ordered[:5] if ordered else selection_assessments[:5]
    
    def _format_recommendations_table(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations as a markdown table."""
        if not recommendations:
            return ""
        
        table = "| # | Name | Test Type | Keys | Duration | Languages | URL |\n"
        table += "|---|------|-----------|------|----------|-----------|-----|\n"
        
        for i, rec in enumerate(recommendations[:5], 1):
            name = rec.get('name', 'Unknown')[:45]
            test_type = rec.get('test_type', 'General')
            keys = ', '.join(rec.get('keys', ['General'])[:2])
            duration = rec.get('duration', '—')
            languages = rec.get('languages', ['English'])[0] if rec.get('languages') else '—'
            # Truncate languages for table
            if len(languages) > 15:
                languages = languages[:12] + "..."
            url = rec.get('url', '#')
            
            table += f"| {i} | {name} | {test_type} | {keys} | {duration} | {languages} | {url} |\n"
        
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
        
        # Extract assessment names
        words = re.findall(r'[A-Za-z0-9\.\+\#\s]+', message)
        candidates = [w.strip() for w in words if len(w.strip()) > 3 and w.strip().lower() not in compare_words]
        
        if len(candidates) >= 2:
            # Find assessments by name
            assessments = []
            for cand in candidates[:2]:
                for a in self.retriever.get_all():
                    if cand.lower() in a.get('name', '').lower():
                        assessments.append(a)
                        break
            
            if len(assessments) >= 2:
                reply = self._format_comparison_table(assessments[0], assessments[1])
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
    
    def _format_comparison_table(self, a1: Dict, a2: Dict) -> str:
        """Format comparison as table."""
        return f"""
| Feature | {a1.get('name', 'Assessment 1')} | {a2.get('name', 'Assessment 2')} |
|---------|-------------------------------|-------------------------------|
| Test Type | {a1.get('test_type', 'N/A')} | {a2.get('test_type', 'N/A')} |
| Duration | {a1.get('duration', 'N/A')} | {a2.get('duration', 'N/A')} |
| Remote Testing | {'Yes' if a1.get('remote_testing') else 'No'} | {'Yes' if a2.get('remote_testing') else 'No'} |
| Adaptive Support | {'Yes' if a1.get('adaptive_support') else 'No'} | {'Yes' if a2.get('adaptive_support') else 'No'} |
| Keys | {', '.join(a1.get('keys', ['N/A'])[:2])} | {', '.join(a2.get('keys', ['N/A'])[:2])} |

**{a1.get('name')}**: {a1.get('link', '#')}
**{a2.get('name')}**: {a2.get('link', '#')}
"""
    
    def process(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process user message and generate response.
        
        Flow:
        - Turn 1: Clarify (no recommendations)
        - Turn 2: Recommend leadership assessments
        - Turn 3: If selection/benchmark, recommend with table
        - Turn 4: Confirm and end conversation
        """
        turn_count = len([m for m in conversation_history if m.get('role') == 'user']) + 1
        
        # Get last assistant response if any (for context)
        last_assistant = ""
        for m in reversed(conversation_history):
            if m.get('role') == 'assistant':
                last_assistant = m.get('content', '')
                break
        
        # 1. REFUSAL CHECK
        refusal = self._should_refuse(message)
        if refusal:
            return {
                'reply': refusal,
                'recommendations': [],
                'end_of_conversation': False
            }
        
        # 2. COMPARISON CHECK
        comparison = self._handle_comparison(message)
        if comparison:
            return comparison
        
        # 3. CONFIRMATION CHECK (Turn 4 or later)
        confirmation_phrases = ['perfect', 'that\'s what we need', 'exactly', 'great', 'good', 'yes', 'perfect, that']
        is_confirmation = any(phrase in message.lower() for phrase in confirmation_phrases)
        
        if is_confirmation and turn_count >= 3:
            # End conversation
            return {
                'reply': "Excellent! The OPQ32r is what your candidates complete — the Leadership and Competency Reports are the outputs you receive, both runnable from a single administration. The details are above. Is there anything else I can help with?",
                'recommendations': [],
                'end_of_conversation': True
            }
        
        message_lower = message.lower()
        
        # 4. TURN 1: First user message - ALWAYS clarify, NEVER recommend
        if turn_count == 1:
            return {
                'reply': "To find the right SHL assessments for you, please provide:\n\n• **Job role** (e.g., Java Developer, Sales Manager, CXO, Director)\n• **Seniority level** (Junior/Senior/Lead/Manager/Executive)\n• **Purpose** (Selection/Development/Benchmarking)\n\nExample: 'I need assessments for selecting senior executives against a leadership benchmark'",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        # 5. TURN 2: Provide leadership recommendations
        if turn_count == 2:
            recommendations = self._get_leadership_assessments()
            if recommendations:
                reply = "Based on your leadership requirements, here are relevant SHL assessments:\n\n" + self._format_recommendations_table(recommendations)
                reply += "\n\n---\n💡 **One more question**: Is this for selection (comparing candidates) or development (feedback for existing leaders)?"
                return {
                    'reply': reply,
                    'recommendations': self._format_recommendations_list(recommendations),
                    'end_of_conversation': False
                }
        
        # 6. TURN 3: Check for selection/benchmark keywords and provide final recommendations
        is_selection = any(word in message_lower for word in ['selection', 'benchmark', 'comparing candidates', 'compare candidates', 'selection — comparing'])
        
        if turn_count == 3:
            if is_selection:
                recommendations = self._get_selection_recommendations()
                if recommendations:
                    reply = "For selection with a leadership benchmark, here are the recommended instruments and reports:\n\n" + self._format_recommendations_table(recommendations)
                    reply += "\n\n---\n💡 The OPQ32r is what candidates complete — the UCF and Leadership Reports are the outputs you receive, both runnable from a single administration."
                    return {
                        'reply': reply,
                        'recommendations': self._format_recommendations_list(recommendations),
                        'end_of_conversation': False
                    }
            else:
                # Not selection, ask for clarification
                return {
                    'reply': "Could you share more about the specific leadership level? (CXO, Director, Manager, etc.) And is this for selection or development?",
                    'recommendations': [],
                    'end_of_conversation': False
                }
        
        # 7. FALLBACK: General search
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