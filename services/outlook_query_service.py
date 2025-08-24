import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .composio_integration import ComposioIntegration

class OutlookQueryService:
    """
    Service to query Outlook messages and attachments using Composio MCP
    before intelligent filtering and download.
    """
    
    def __init__(self, composio_integration: ComposioIntegration):
        self.composio = composio_integration
        
    async def search_messages_with_attachments(
        self,
        sender_email: Optional[str] = None,
        email_subject: Optional[str] = None,
        days_back: int = 7,
        max_messages: int = 20
    ) -> Dict[str, Any]:
        """
        Search Outlook messages with attachments based on criteria.
        
        Args:
            sender_email: Email address to search from
            email_subject: Subject keywords to search for
            days_back: Number of days to look back
            max_messages: Maximum number of messages to return
            
        Returns:
            Dict with messages and their attachments
        """
        try:
            print(f"🔍 Querying Outlook messages with attachments...")
            print(f"📋 Search criteria: sender='{sender_email}', subject='{email_subject}', days_back={days_back}")
            
            # Step 1: Initialize MCP connection
            init_response = await self.composio._send_mcp_request("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "outlook-query-client",
                    "version": "1.0.0"
                }
            })
            
            # Step 2: Get available tools
            tools_response = await self.composio._send_mcp_request("tools/list", {})
            
            # Step 3: Find message listing tools
            message_tools = []
            if "result" in tools_response and "tools" in tools_response["result"]:
                for tool in tools_response["result"]["tools"]:
                    tool_name = tool.get("name", "").lower()
                    if any(keyword in tool_name for keyword in ["list_messages", "search_messages", "outlook_list", "outlook_search"]):
                        message_tools.append(tool)
                        print(f"📧 Found message tool: {tool['name']}")
            
            # Step 4: Prepare search parameters
            search_params = self._prepare_search_params(
                sender_email, email_subject, days_back, max_messages
            )
            
            # Step 5: Try different message listing approaches
            messages_data = []
            
            # Approach 1: Try OUTLOOK_OUTLOOK_LIST_MESSAGES
            try:
                list_response = await self.composio._send_mcp_request("tools/call", {
                    "name": "OUTLOOK_OUTLOOK_LIST_MESSAGES",
                    "arguments": search_params
                })
                
                if self._is_successful_response(list_response):
                    messages_data = self._extract_messages_from_response(list_response)
                    print(f"✅ Found {len(messages_data)} messages using OUTLOOK_OUTLOOK_LIST_MESSAGES")
                
            except Exception as e:
                print(f"⚠️ OUTLOOK_OUTLOOK_LIST_MESSAGES failed: {e}")
            
            # Approach 2: Try OUTLOOK_OUTLOOK_SEARCH_MESSAGES if first approach failed
            if not messages_data:
                try:
                    search_response = await self.composio._send_mcp_request("tools/call", {
                        "name": "OUTLOOK_OUTLOOK_SEARCH_MESSAGES",
                        "arguments": search_params
                    })
                    
                    if self._is_successful_response(search_response):
                        messages_data = self._extract_messages_from_response(search_response)
                        print(f"✅ Found {len(messages_data)} messages using OUTLOOK_OUTLOOK_SEARCH_MESSAGES")
                        
                except Exception as e:
                    print(f"⚠️ OUTLOOK_OUTLOOK_SEARCH_MESSAGES failed: {e}")
            
            # Step 6: For each message, get attachment details
            enriched_messages = []
            for message in messages_data[:max_messages]:
                try:
                    enriched_message = await self._get_message_with_attachments(message)
                except Exception as e:
                    print(f"⚠️ Failed to get detailed message for {message.get('id', 'unknown')}: {e}")
                    enriched_message = message

                # Always attempt LIST_ATTACHMENTS to ensure we capture attachments even if previous call failed
                try:
                    msg_id = enriched_message.get('id') or message.get('id')
                    if msg_id:
                        attachments_resp = await self.composio._send_mcp_request("tools/call", {
                            "name": "OUTLOOK_LIST_OUTLOOK_ATTACHMENTS",
                            "arguments": {"message_id": msg_id, "messageId": msg_id}
                        })
                        if self._is_successful_response(attachments_resp):
                            attachments = self._extract_attachments_from_response(attachments_resp)
                            if attachments:
                                enriched_message['attachments'] = attachments
                                print(f"📎 Added {len(attachments)} attachments via separate LIST_ATTACHMENTS call")
                except Exception as e:
                    print(f"⚠️ LIST_ATTACHMENTS failed for message {message.get('id', 'unknown')}: {e}")

                if enriched_message.get('attachments'):
                    enriched_messages.append(enriched_message)
            
            result = {
                'status': 'success',
                'total_messages': len(messages_data),
                'messages_with_attachments': len(enriched_messages),
                'messages': enriched_messages,
                'search_params': search_params,
                'query_timestamp': datetime.utcnow().isoformat()
            }
            
            print(f"📊 Query complete: {len(enriched_messages)} messages with attachments found")
            return result
            
        except Exception as e:
            print(f"❌ Outlook query error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total_messages': 0,
                'messages_with_attachments': 0,
                'messages': []
            }
    
    def _prepare_search_params(
        self, 
        sender_email: Optional[str], 
        email_subject: Optional[str], 
        days_back: int, 
        max_messages: int
    ) -> Dict[str, Any]:
        """Prepare search parameters for Outlook MCP tools."""
        params = {
            'limit': max_messages,
            'include_attachments': True,
            'days_back': days_back
        }
        
        # Handle sender email
        if sender_email:
            if sender_email.startswith('from:'):
                sender_clean = sender_email[5:]
            else:
                sender_clean = sender_email
            
            params.update({
                'sender': sender_clean,
                'from': sender_clean,
                'sender_email': sender_clean,
                'from_email': sender_clean
            })
        
        # Handle subject search
        if email_subject:
            params.update({
                'subject': email_subject,
                'email_subject': email_subject,
                'query': email_subject,
                'search_query': email_subject
            })
        
        # Add time constraints
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        params.update({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'received_after': start_date.isoformat(),
            'received_before': end_date.isoformat()
        })
        
        return params
    
    async def _get_message_with_attachments(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed message information including attachments."""
        try:
            message_id = message.get('id')
            if not message_id:
                return message
            
            # Try to get message details with attachments
            detail_response = await self.composio._send_mcp_request("tools/call", {
                "name": "OUTLOOK_OUTLOOK_GET_MESSAGE",
                "arguments": {
                    'message_id': message_id,
                    'messageId': message_id,
                    'id': message_id,
                    'include_attachments': True,
                    'expand_attachments': True
                }
            })
            
            if self._is_successful_response(detail_response):
                detailed_message = self._extract_message_from_response(detail_response)
                if detailed_message:
                    return detailed_message
            
            # Fallback: Try to list attachments separately
            try:
                attachments_response = await self.composio._send_mcp_request("tools/call", {
                    "name": "OUTLOOK_LIST_OUTLOOK_ATTACHMENTS",
                    "arguments": {
                        'message_id': message_id,
                        'messageId': message_id
                    }
                })
                
                if self._is_successful_response(attachments_response):
                    attachments = self._extract_attachments_from_response(attachments_response)
                    message['attachments'] = attachments
                    
            except Exception as e:
                print(f"⚠️ Failed to get attachments for message {message_id}: {e}")
            
            return message
            
        except Exception as e:
            print(f"⚠️ Error getting message details: {e}")
            return message
    
    def _is_successful_response(self, response: Dict[str, Any]) -> bool:
        """Check if MCP response indicates success."""
        if not response:
            return False
            
        # Check for MCP error
        if 'error' in response:
            return False
            
        # Check for result content
        result = response.get('result', {})
        if not result:
            return False
            
        # Check for tool execution success
        content = result.get('content', [])
        if not content:
            return False
            
        # Check if any content indicates success
        for item in content:
            if item.get('type') == 'text':
                text = item.get('text', '')
                try:
                    data = json.loads(text)
                    if data.get('successful', False) or data.get('data'):
                        return True
                except:
                    # If not JSON, consider non-empty text as potentially successful
                    if text.strip():
                        return True
        
        return False
    
    def _extract_messages_from_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract messages from MCP response."""
        messages = []
        
        try:
            result = response.get('result', {})
            content = result.get('content', [])
            
            for item in content:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    try:
                        data = json.loads(text)
                        
                        # Handle different response formats
                        if 'data' in data:
                            data_content = data['data']
                            if isinstance(data_content, list):
                                messages.extend(data_content)
                            elif isinstance(data_content, dict):
                                if 'messages' in data_content:
                                    messages.extend(data_content['messages'])
                                elif 'value' in data_content:
                                    messages.extend(data_content['value'])
                                else:
                                    messages.append(data_content)
                        elif 'messages' in data:
                            messages.extend(data['messages'])
                        elif 'value' in data:
                            messages.extend(data['value'])
                        elif isinstance(data, list):
                            messages.extend(data)
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error extracting messages: {e}")
        
        return messages
    
    def _extract_message_from_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract single message from MCP response."""
        messages = self._extract_messages_from_response(response)
        return messages[0] if messages else None
    
    def _extract_attachments_from_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachments from MCP response."""
        attachments = []
        
        try:
            result = response.get('result', {})
            content = result.get('content', [])
            
            for item in content:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    try:
                        data = json.loads(text)
                        
                        if 'data' in data:
                            data_content = data['data']
                            if isinstance(data_content, list):
                                attachments.extend(data_content)
                            elif isinstance(data_content, dict) and 'attachments' in data_content:
                                attachments.extend(data_content['attachments'])
                        elif 'attachments' in data:
                            attachments.extend(data['attachments'])
                        elif isinstance(data, list):
                            attachments.extend(data)
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error extracting attachments: {e}")
        
        return attachments
