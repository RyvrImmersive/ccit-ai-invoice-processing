from typing import Any, Dict, List, Optional
import httpx
import asyncio
import json
import os
import pandas as pd
from datetime import datetime, timedelta

from langflow.custom import Component
from langflow.io import Output, StrInput, IntInput, SecretStrInput
from langflow.schema import Data


class ComposioOutlookFetcher(Component):
    """
    Langflow Custom Component: Composio Outlook Email Fetcher
    
    Fetches Outlook emails using Composio's platform API.
    Uses auth config and connection-based authentication.
    """
    
    display_name = "Composio Outlook Email Fetcher"
    description = "Fetch Outlook emails using Composio's platform API with auth config"
    icon = "mail"
    name = "ComposioOutlookFetcher"
    
    inputs = [
        SecretStrInput(
            name="composio_api_key",
            display_name="Composio API Key",
            info="Your Composio API key from platform.composio.dev",
            value="",
        ),
        StrInput(
            name="composio_base_url",
            display_name="Composio Base URL",
            info="Composio platform API base URL",
            value="https://backend.composio.dev",
        ),
        StrInput(
            name="entity_id",
            display_name="Entity ID",
            info="Composio entity ID (user identifier)",
            value="userJS1",
        ),
        StrInput(
            name="connected_account_id",
            display_name="Connected Account ID",
            info="Composio connected account ID (e.g., ca_tn0qoy_lQUdY from your dashboard)",
            value="ca_tn0qoy_lQUdY",
        ),
        StrInput(
            name="sender_email",
            display_name="Sender Email",
            info="Filter by sender email address (optional)",
            value="",
        ),
        StrInput(
            name="email_subject",
            display_name="Email Subject",
            info="Filter by email subject (optional)", 
            value="",
        ),
        IntInput(
            name="days_back",
            display_name="Days Back",
            info="Number of days back to search",
            value=7,
        ),
        IntInput(
            name="max_messages", 
            display_name="Max Messages",
            info="Maximum number of messages to fetch",
            value=10,
        ),
    ]
    
    outputs = [
        Output(display_name="DataFrame", name="dataframe", method="fetch_messages"),
    ]

    def fetch_messages(self) -> Data:
        """Fetch Outlook messages using Composio's platform API."""
        
        try:
            # Get values from inputs or environment variables
            api_key = self.composio_api_key or os.getenv("COMPOSIO_API_KEY", "")
            base_url = self.composio_base_url or "https://backend.composio.dev/api"
            entity_id = self.entity_id or "default_user"
            connection_id = self.connected_account_id or ""
            
            # Validate required parameters
            if not api_key:
                raise ValueError("Composio API key is required (set composio_api_key input or COMPOSIO_API_KEY env var)")
            
            # Run async operation in sync context
            messages = asyncio.run(self._query_outlook_messages(
                api_key=api_key,
                base_url=base_url,
                entity_id=entity_id,
                connection_id=connection_id,
                sender_email=self.sender_email or None,
                email_subject=self.email_subject or None,
                days_back=self.days_back or 7,
                max_messages=self.max_messages or 10,
            ))
            
            # Convert to DataFrame
            if messages:
                # Flatten message data for DataFrame
                flattened_messages = []
                for message in messages:
                    # Create base message data
                    base_data = {
                        'id': message.get('id', ''),
                        'subject': message.get('subject', ''),
                        'sender': self._extract_email_address(message.get('from', {})),
                        'sender_name': self._extract_sender_name(message.get('from', {})),
                        'received_datetime': message.get('receivedDateTime', ''),
                        'created_datetime': message.get('createdDateTime', ''),
                        'body_preview': message.get('bodyPreview', ''),
                        'importance': message.get('importance', ''),
                        'is_read': message.get('isRead', False),
                        'has_attachments': message.get('hasAttachments', False),
                        'web_link': message.get('webLink', ''),
                        'conversation_id': message.get('conversationId', ''),
                    }
                    
                    # Add attachment information if present
                    attachments = message.get('attachments', [])
                    if attachments:
                        base_data['attachment_count'] = len(attachments)
                        for i, attachment in enumerate(attachments):
                            attachment_data = base_data.copy()
                            attachment_data.update({
                                'attachment_id': attachment.get('id', ''),
                                'attachment_name': attachment.get('name', ''),
                                'attachment_size': attachment.get('size', 0),
                                'attachment_content_type': attachment.get('contentType', ''),
                                'attachment_index': i
                            })
                            flattened_messages.append(attachment_data)
                    else:
                        # Add message without attachments
                        base_data.update({
                            'attachment_count': 0,
                            'attachment_id': '',
                            'attachment_name': '',
                            'attachment_size': 0,
                            'attachment_content_type': '',
                            'attachment_index': -1
                        })
                        flattened_messages.append(base_data)
                
                df = pd.DataFrame(flattened_messages)
                
                # Convert datetime columns
                datetime_columns = ['received_datetime', 'created_datetime']
                for col in datetime_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Sort by received datetime
                if 'received_datetime' in df.columns:
                    df = df.sort_values('received_datetime', ascending=False)
                
            else:
                # Create empty DataFrame with expected columns
                df = pd.DataFrame(columns=[
                    'id', 'subject', 'sender', 'sender_name', 'received_datetime', 
                    'created_datetime', 'body_preview', 'importance', 'is_read',
                    'has_attachments', 'attachment_count', 'web_link', 'conversation_id',
                    'attachment_id', 'attachment_name', 'attachment_size',
                    'attachment_content_type', 'attachment_index'
                ])
            
            # Convert DataFrame to dictionary format for Langflow Data
            dataframe_dict = {
                "dataframe": df.to_dict('records'),  # Convert to list of dictionaries
                "columns": df.columns.tolist(),
                "shape": df.shape,
                "dtypes": df.dtypes.astype(str).to_dict() if not df.empty else {},
                "summary": {
                    "total_messages": len(df['id'].unique()) if 'id' in df.columns and not df.empty else 0,
                    "total_attachments": len(df[df['attachment_index'] >= 0]) if 'attachment_index' in df.columns and not df.empty else 0,
                    "date_range": {
                        "earliest": df['received_datetime'].min().isoformat() if 'received_datetime' in df.columns and not df.empty and df['received_datetime'].notna().any() else None,
                        "latest": df['received_datetime'].max().isoformat() if 'received_datetime' in df.columns and not df.empty and df['received_datetime'].notna().any() else None,
                    }
                }
            }
            
            return Data(data=dataframe_dict)
            
        except Exception as e:
            # Return error as dictionary
            error_dict = {
                "error": True,
                "message": f"Error fetching Outlook messages: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "dataframe": [],
                "columns": [],
                "shape": [0, 0]
            }
            return Data(data=error_dict)

    def _extract_email_address(self, from_field: Any) -> str:
        """Extract email address from various from field formats."""
        if isinstance(from_field, dict):
            if 'emailAddress' in from_field:
                email_addr = from_field['emailAddress']
                if isinstance(email_addr, dict):
                    return email_addr.get('address', '')
                return str(email_addr)
            return from_field.get('address', '')
        return str(from_field) if from_field else ''

    def _extract_sender_name(self, from_field: Any) -> str:
        """Extract sender name from various from field formats."""
        if isinstance(from_field, dict):
            if 'emailAddress' in from_field:
                email_addr = from_field['emailAddress']
                if isinstance(email_addr, dict):
                    return email_addr.get('name', '')
            return from_field.get('name', '')
        return ''

    async def _query_outlook_messages(
        self,
        api_key: str,
        base_url: str,
        entity_id: str,
        connection_id: str,
        sender_email: Optional[str] = None,
        email_subject: Optional[str] = None,
        days_back: int = 7,
        max_messages: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query Outlook messages via Composio platform API."""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
            }
            
            # Build search parameters for Outlook API
            search_params = {}
            
            # Add basic parameters
            if max_messages:
                search_params["$top"] = max_messages
            
            search_params["$orderby"] = "receivedDateTime desc"
            search_params["$select"] = "id,subject,from,receivedDateTime,createdDateTime,bodyPreview,importance,isRead,hasAttachments,webLink,conversationId"
            
            # Build filter conditions
            filter_conditions = []
            
            # Add date filter
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            filter_conditions.append(f"receivedDateTime ge {start_date.isoformat()}")
            
            # Add sender filter if provided
            if sender_email:
                sender_clean = sender_email.replace('from:', '').strip() if sender_email.startswith('from:') else sender_email.strip()
                filter_conditions.append(f"from/emailAddress/address eq '{sender_clean}'")
            
            # Add subject filter if provided (using contains for partial match)
            if email_subject:
                filter_conditions.append(f"contains(subject,'{email_subject}')")
            
            # Combine filters
            if filter_conditions:
                search_params["$filter"] = " and ".join(filter_conditions)
            
            # Prepare the request payload for Composio's v3 API
            request_payload = {
                "entityId": entity_id,
                "connectedAccountId": connection_id,
                "arguments": search_params
            }
            
            # Execute the action using v2 API (try correct endpoint)
            response = await client.post(
                f"{base_url}/api/v2/actions/execute",
                json={
                    "entityId": entity_id,
                    "connectedAccountId": connection_id,
                    "appName": "outlook",
                    "actionName": "OUTLOOK_OUTLOOK_LIST_MESSAGES",
                    "params": search_params
                },
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Composio API request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Handle different response formats
            if "error" in result or not result.get("successfull", result.get("success", False)):
                error_msg = result.get("error", result.get("message", "Unknown error"))
                raise Exception(f"Composio API error: {error_msg}")
            
            # Extract messages from result - try different response formats
            messages_data = []
            if "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    messages_data = data
                elif isinstance(data, dict):
                    # Try Microsoft Graph API response format
                    if "value" in data:
                        messages_data = data["value"]
                    # Try other formats
                    elif "messages" in data:
                        messages_data = data["messages"]
                    else:
                        messages_data = [data]
            elif "response" in result:
                response_data = result["response"]
                if isinstance(response_data, dict) and "value" in response_data:
                    messages_data = response_data["value"]
                elif isinstance(response_data, list):
                    messages_data = response_data
            
            # Ensure we have a list
            if not isinstance(messages_data, list):
                messages_data = []
            
            # For each message, try to get attachments if hasAttachments is true
            enriched_messages = []
            for message in messages_data[:max_messages]:
                if message.get('hasAttachments', False):
                    try:
                        # Get attachments for this message
                        attachment_payload = {
                            "entityId": entity_id,
                            "connectedAccountId": connection_id,
                            "arguments": {
                                "messageId": message.get('id')
                            }
                        }
                        
                        attach_response = await client.post(
                            f"{base_url}/api/v2/actions/execute",
                            json={
                                "entityId": entity_id,
                                "connectedAccountId": connection_id,
                                "appName": "outlook",
                                "actionName": "LIST_OUTLOOK_ATTACHMENTS",
                                "params": {"messageId": message.get('id')}
                            },
                            headers=headers
                        )
                        
                        if attach_response.status_code in [200, 201]:
                            attach_result = attach_response.json()
                            if attach_result.get("successfull", attach_result.get("success", False)):
                                attachments_data = attach_result.get("data", [])
                                if isinstance(attachments_data, dict):
                                    if "value" in attachments_data:
                                        attachments = attachments_data["value"]
                                    elif "attachments" in attachments_data:
                                        attachments = attachments_data["attachments"]
                                    else:
                                        attachments = [attachments_data]
                                elif isinstance(attachments_data, list):
                                    attachments = attachments_data
                                else:
                                    attachments = []
                                message['attachments'] = attachments
                            else:
                                message['attachments'] = []
                        else:
                            message['attachments'] = []
                            
                    except Exception:
                        # Continue even if attachment fetching fails
                        message['attachments'] = []
                else:
                    message['attachments'] = []
                
                enriched_messages.append(message)
            
            return enriched_messages