import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class IntelligentAgent:
    """
    Intelligent agent to analyze Outlook messages and attachments,
    filter relevant items, and provide specific IDs for download.
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
        
    async def analyze_and_filter_attachments(
        self,
        messages_data: List[Dict[str, Any]],
        search_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze messages and attachments to identify the best match for download.
        
        Args:
            messages_data: List of messages with attachments from Outlook
            search_criteria: Original search parameters (sender, subject, attachment_name, etc.)
            
        Returns:
            Dict with filtered attachment details and confidence scores
        """
        try:
            print(f"🤖 Intelligent Agent: Analyzing {len(messages_data)} messages...")
            
            # Extract search criteria with safe null handling
            target_sender = (search_criteria.get('sender_email') or '').lower()
            target_subject = (search_criteria.get('email_subject') or '').lower()
            target_attachment = (search_criteria.get('attachment_name') or '').lower()
            days_back = search_criteria.get('days_back', 7)
            
            candidates = []
            
            for message in messages_data:
                message_score = self._score_message(message, search_criteria)
                
                # Analyze attachments in this message
                attachments = message.get('attachments', [])
                for attachment in attachments:
                    attachment_score = self._score_attachment(attachment, search_criteria)
                    
                    # Combined confidence score
                    total_score = (message_score + attachment_score) / 2
                    
                    candidate = {
                        'message_id': message.get('id'),
                        'attachment_id': attachment.get('id'),
                        'attachment_name': attachment.get('name'),
                        'message_subject': message.get('subject'),
                        'sender_email': message.get('from', {}).get('emailAddress', {}).get('address'),
                        'received_date': message.get('receivedDateTime'),
                        'attachment_size': attachment.get('size'),
                        'attachment_type': attachment.get('contentType'),
                        'confidence_score': total_score,
                        'match_reasons': self._get_match_reasons(message, attachment, search_criteria)
                    }
                    
                    candidates.append(candidate)
            
            # Sort by confidence score
            candidates.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Filter high-confidence matches
            high_confidence_matches = [
                c for c in candidates 
                if c['confidence_score'] >= self.confidence_threshold
            ]
            
            result = {
                'status': 'success',
                'total_candidates': len(candidates),
                'high_confidence_matches': len(high_confidence_matches),
                'recommended_attachment': candidates[0] if candidates else None,
                'all_candidates': candidates[:5],  # Top 5 candidates
                'search_criteria': search_criteria,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            if candidates:
                best_match = candidates[0]
                print(f"✅ Best match found: {best_match['attachment_name']} (confidence: {best_match['confidence_score']:.2f})")
            else:
                print("⚠️ No suitable attachments found")
                
            return result
            
        except Exception as e:
            print(f"❌ Intelligent Agent error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total_candidates': 0,
                'recommended_attachment': None
            }
    
    def _score_message(self, message: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Score a message based on how well it matches search criteria."""
        score = 0.0
        max_score = 0.0
        
        # Sender email matching
        if criteria.get('sender_email'):
            max_score += 1.0
            sender_addr = message.get('from', {}).get('emailAddress', {}).get('address') or ''
            sender_addr = sender_addr.lower() if sender_addr else ''
            target_sender = (criteria['sender_email'] or '').lower()
            
            if target_sender.startswith('from:'):
                target_sender = target_sender[5:]
            
            if target_sender and sender_addr and target_sender in sender_addr:
                score += 1.0
            elif target_sender and sender_addr and any(part in sender_addr for part in target_sender.split('@') if part):
                score += 0.5
        
        # Subject matching
        if criteria.get('email_subject'):
            max_score += 1.0
            subject = message.get('subject') or ''
            subject = subject.lower() if subject else ''
            target_subject = (criteria['email_subject'] or '').lower()
            
            # Exact match
            if target_subject and subject and target_subject in subject:
                score += 1.0
            # Partial word matching
            elif target_subject and subject and any(word in subject for word in target_subject.split() if word and len(word) > 2):
                score += 0.6
        
        # Date relevance (more recent = higher score)
        if message.get('receivedDateTime'):
            max_score += 0.5
            try:
                received_date = datetime.fromisoformat(message['receivedDateTime'].replace('Z', '+00:00'))
                days_ago = (datetime.now(received_date.tzinfo) - received_date).days
                days_back = criteria.get('days_back', 7)
                
                if days_ago <= days_back:
                    # More recent messages get higher scores
                    score += 0.5 * (1 - (days_ago / days_back))
            except:
                pass
        
        return score / max_score if max_score > 0 else 0.0
    
    def _score_attachment(self, attachment: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Score an attachment based on how well it matches search criteria."""
        score = 0.0
        max_score = 0.0
        
        attachment_name = attachment.get('name') or ''
        attachment_name = attachment_name.lower() if attachment_name else ''
        
        # Attachment name matching
        if criteria.get('attachment_name'):
            max_score += 1.0
            target_name = (criteria['attachment_name'] or '').lower()
            
            # Handle JSON format like {"filename": "invoice.pdf"}
            if target_name.startswith('{') and target_name.endswith('}'):
                try:
                    name_obj = json.loads(criteria['attachment_name'])
                    target_name = (name_obj.get('filename') or target_name).lower()
                except:
                    pass
            
            # Exact filename match
            if target_name and attachment_name and target_name == attachment_name:
                score += 1.0
            # Partial filename match
            elif target_name and attachment_name and (target_name in attachment_name or attachment_name in target_name):
                score += 0.8
            # Extension match
            elif target_name and attachment_name and '.' in target_name and '.' in attachment_name:
                target_ext = target_name.split('.')[-1]
                attach_ext = attachment_name.split('.')[-1]
                if target_ext == attach_ext:
                    score += 0.3
        
        # File type preferences (PDFs often contain important data)
        max_score += 0.3
        content_type = attachment.get('contentType') or ''
        content_type = content_type.lower() if content_type else ''
        if 'pdf' in content_type:
            score += 0.3
        elif any(doc_type in content_type for doc_type in ['word', 'excel', 'document']):
            score += 0.2
        elif 'image' in content_type:
            score += 0.1
        
        # File size reasonableness (not too small, not too large)
        max_score += 0.2
        size = attachment.get('size', 0)
        if 1000 <= size <= 10_000_000:  # 1KB to 10MB
            score += 0.2
        elif 100 <= size <= 50_000_000:  # 100B to 50MB
            score += 0.1
        
        return score / max_score if max_score > 0 else 0.0
    
    def _get_match_reasons(
        self, 
        message: Dict[str, Any], 
        attachment: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasons why this attachment was matched."""
        reasons = []
        
        # Sender matching
        if criteria.get('sender_email'):
            sender_addr = message.get('from', {}).get('emailAddress', {}).get('address') or ''
            target_sender = (criteria['sender_email'] or '').replace('from:', '')
            if target_sender and sender_addr and target_sender.lower() in sender_addr.lower():
                reasons.append(f"Sender matches: {sender_addr}")
        
        # Subject matching
        if criteria.get('email_subject'):
            subject = message.get('subject') or ''
            email_subject = criteria['email_subject'] or ''
            if email_subject and subject and email_subject.lower() in subject.lower():
                reasons.append(f"Subject contains: '{email_subject}'")
        
        # Attachment name matching
        if criteria.get('attachment_name'):
            attachment_name = attachment.get('name') or ''
            target_name = criteria['attachment_name'] or ''
            if target_name and attachment_name and target_name.lower() in attachment_name.lower():
                reasons.append(f"Filename matches: {attachment_name}")
        
        # File type
        content_type = attachment.get('contentType', '')
        if content_type:
            reasons.append(f"File type: {content_type}")
        
        # Date
        if message.get('receivedDateTime'):
            reasons.append(f"Received: {message['receivedDateTime']}")
        
        return reasons
    
    def extract_best_match_params(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the best match parameters for Composio download.
        
        Returns:
            Dict with attachment_id, message_id, attachment_name for download
        """
        if analysis_result.get('status') != 'success':
            return {
                'status': 'error',
                'error': 'Analysis failed',
                'attachment_id': None,
                'message_id': None,
                'attachment_name': None
            }
        
        recommended = analysis_result.get('recommended_attachment')
        if not recommended:
            return {
                'status': 'error',
                'error': 'No suitable attachment found',
                'attachment_id': None,
                'message_id': None,
                'attachment_name': None
            }
        
        return {
            'status': 'success',
            'attachment_id': recommended['attachment_id'],
            'message_id': recommended['message_id'],
            'attachment_name': recommended['attachment_name'],
            'confidence_score': recommended['confidence_score'],
            'match_reasons': recommended['match_reasons'],
            'sender_email': recommended['sender_email'],
            'message_subject': recommended['message_subject']
        }
