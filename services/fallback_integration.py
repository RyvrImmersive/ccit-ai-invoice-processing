import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class FallbackIntegration:
    """
    Fallback integration for demonstration purposes.
    This provides a working API structure with mock responses.
    """
    
    def __init__(self):
        # No environment variables required - this is a fallback demo service
        pass
    
    async def download_outlook_attachment(
        self,
        email_subject: str = None,
        attachment_name: str = None,
        sender_email: Optional[str] = None,
        days_back: int = 7,
        attachment_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback implementation for downloading Outlook attachments.
        Returns a structured response indicating the current integration status.
        """
        since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return {
            "status": "integration_pending",
            "message": "Composio MCP integration is being configured. This is a fallback response.",
            "request_details": {
                "email_subject": email_subject,
                "attachment_name": attachment_name,
                "sender_email": sender_email,
                "days_back": days_back,
                "since_date": since_date,
                "attachment_id": attachment_id,
                "message_id": message_id
            },
            "composio_config": {
                "server_id": self.server_id,
                "user_id": self.user_id,
                "api_key_present": bool(self.api_key)
            },
            "outlook_parameters": {
                "attachment_id_provided": bool(attachment_id),
                "message_id_provided": bool(message_id),
                "attachment_id_length": len(attachment_id) if attachment_id else 0,
                "message_id_format": "hex" if message_id and all(c in '0123456789abcdef' for c in message_id.lower()) else "unknown"
            },
            "next_steps": [
                "Verify Composio MCP server endpoint configuration",
                "Confirm correct authentication method for MCP protocol", 
                "Test with proper MCP client library or direct protocol implementation",
                "Use provided attachment_id and message_id for direct Outlook Graph API access"
            ]
        }
    
    async def list_emails(
        self,
        email_subject: Optional[str] = None,
        sender_email: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Fallback implementation for listing emails.
        Returns a structured response indicating the current integration status.
        """
        since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return {
            "status": "integration_pending",
            "message": "Composio MCP integration is being configured. This is a fallback response.",
            "request_details": {
                "email_subject": email_subject,
                "sender_email": sender_email,
                "days_back": days_back,
                "since_date": since_date
            },
            "composio_config": {
                "server_id": self.server_id,
                "user_id": self.user_id,
                "api_key_present": bool(self.api_key)
            },
            "demo_emails": [
                {
                    "id": "demo_email_1",
                    "subject": f"Demo: {email_subject or 'Sample Email'}",
                    "sender": sender_email or "demo@example.com",
                    "received_date": since_date,
                    "has_attachments": True,
                    "attachments": ["demo_attachment.pdf", "sample_file.xlsx"]
                }
            ]
        }
