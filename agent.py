def process(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Process user message and generate response.
    
    Flow:
    - Turn 1: Clarify (no recommendations)
    - Turn 2: Recommend leadership assessments  
    - Turn 3: If selection/benchmark, recommend with table
    - Turn 4: Confirm and end conversation
    - REFINEMENT: If user says "add X" or "actually", update recommendations
    """
    turn_count = len([m for m in conversation_history if m.get('role') == 'user']) + 1
    
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
    
    # 3. REFINEMENT CHECK - NEW!
    refinement_keywords = ['actually', 'add', 'instead', 'also include', 'plus', 'and also', 'refine', 'change']
    is_refinement = any(keyword in message.lower() for keyword in refinement_keywords)
    
    # Check if previous assistant response had recommendations
    last_assistant_recs = []
    for msg in reversed(conversation_history):
        if msg.get('role') == 'assistant' and 'recommendations' in msg:
            last_assistant_recs = msg.get('recommendations', [])
            break
    
    if is_refinement and last_assistant_recs:
        # User wants to refine previous recommendations
        refinement_type = None
        if 'personality' in message.lower():
            refinement_type = 'personality'
        elif 'cognitive' in message.lower():
            refinement_type = 'cognitive'
        elif 'cheaper' in message.lower() or 'budget' in message.lower():
            refinement_type = 'budget'
        
        if refinement_type == 'personality':
            # Add personality assessments to the mix
            personality_assessments = []
            for a in self.retriever.get_all():
                if 'Personality' in a.get('keys', []) or 'personality' in a.get('test_type', '').lower():
                    if a not in personality_assessments:
                        personality_assessments.append(a)
            
            combined = last_assistant_recs[:3] + personality_assessments[:2]
            # Remove duplicates
            seen = set()
            unique_recs = []
            for rec in combined:
                rec_id = rec.get('id') or rec.get('name')
                if rec_id not in seen:
                    seen.add(rec_id)
                    unique_recs.append(rec)
            
            return {
                'reply': "I've added personality assessments to your recommendations:\n\n" + self._format_recommendations_table(unique_recs),
                'recommendations': self._format_recommendations_list(unique_recs),
                'end_of_conversation': False
            }
    
    # 4. CONFIRMATION CHECK (Turn 4 or later)
    confirmation_phrases = ['perfect', 'that\'s what we need', 'exactly', 'great', 'good', 'yes']
    is_confirmation = any(phrase in message.lower() for phrase in confirmation_phrases)
    
    if is_confirmation and turn_count >= 3:
        return {
            'reply': "Excellent! The OPQ32r is what your candidates complete — the Leadership and Competency Reports are the outputs you receive, both runnable from a single administration. The details are above. Is there anything else I can help with?",
            'recommendations': [],
            'end_of_conversation': True
        }
    
    # 5. TURN 1: First user message - ALWAYS clarify, NEVER recommend
    if turn_count == 1:
        return {
            'reply': "To find the right SHL assessments for you, please provide:\n\n• **Job role** (e.g., Java Developer, Sales Manager, CXO, Director)\n• **Seniority level** (Junior/Senior/Lead/Manager/Executive)\n• **Purpose** (Selection/Development/Benchmarking)\n\nExample: 'I need assessments for selecting senior executives against a leadership benchmark'",
            'recommendations': [],
            'end_of_conversation': False
        }
    
    # 6. TURN 2: Provide recommendations based on context
    if turn_count == 2:
        # Check if Java developer or similar
        if 'java' in message.lower() or 'developer' in message.lower():
            recommendations, status = self.retriever.get_recommendations(message, max_results=5)
        else:
            recommendations = self._get_leadership_assessments()
        
        if recommendations:
            reply = "Based on your requirements, here are relevant SHL assessments:\n\n" + self._format_recommendations_table(recommendations)
            reply += "\n\n---\n💡 **One more question**: Is this for selection (comparing candidates) or development (feedback for existing leaders)?"
            return {
                'reply': reply,
                'recommendations': self._format_recommendations_list(recommendations),
                'end_of_conversation': False
            }
    
    # 7. TURN 3: Check for selection/benchmark keywords
    is_selection = any(word in message.lower() for word in ['selection', 'benchmark', 'comparing candidates', 'compare candidates'])
    
    if turn_count == 3:
        if is_selection:
            recommendations = self._get_selection_recommendations()
            if recommendations:
                reply = "For selection with a leadership benchmark, here are the recommended instruments and reports:\n\n" + self._format_recommendations_table(recommendations)
                return {
                    'reply': reply,
                    'recommendations': self._format_recommendations_list(recommendations),
                    'end_of_conversation': False
                }
    
    # 8. FALLBACK: General search
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