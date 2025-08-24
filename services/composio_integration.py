import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

class ComposioIntegration:
    def __init__(self, api_key: str = None, base_url: str = None, server_id: str = None, user_id: str = None):
        self.base_url = base_url or "https://mcp.composio.dev"
        self.server_id = server_id or "76b9c7a4-85bc-4711-a848-f0d56fde2a5a"
        self.user_id = user_id or "userJS1"
        self.api_key = api_key
        
        # Construct the MCP endpoint URL (Streamable HTTP)
        self.mcp_endpoint = f"{self.base_url}/composio/server/{self.server_id}/mcp?user_id={self.user_id}"
        
        # Initialize session for connection reuse
        self.session = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session for MCP communication"""
        if self.session is None or self.session.is_closed:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Outlook-MCP-Client/1.0"
                }
            )
        return self.session
        
    async def _send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the Composio MCP server using Streamable HTTP transport
        """
        request_id = str(uuid.uuid4())
        
        # JSON-RPC 2.0 payload
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        try:
            session = await self._get_session()
            
            print(f"🔄 Sending MCP request: {method} to {self.mcp_endpoint}")
            print(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            response = await session.post(
                self.mcp_endpoint,
                json=payload,
                headers=headers
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if not response.is_success:
                error_text = response.text
                print(f"❌ HTTP Error {response.status_code}: {error_text}")
                raise Exception(f"HTTP {response.status_code}: {error_text}")
            
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                # Direct JSON response
                result = response.json()
                print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                return result
                
            elif "text/event-stream" in content_type:
                # SSE stream response
                print("📡 Processing SSE stream...")
                return await self._process_sse_stream(response, request_id)
                
            else:
                raise Exception(f"Unexpected content type: {content_type}")
                
        except httpx.RequestError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            print(f"❌ MCP request failed: {str(e)}")
            raise Exception(f"MCP request failed: {str(e)}")
    
    async def _process_sse_stream(self, response: httpx.Response, request_id: str) -> Dict[str, Any]:
        """Process Server-Sent Events stream from MCP server"""
        try:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip():
                        try:
                            message = json.loads(data)
                            print(f"📨 SSE Message: {json.dumps(message, indent=2)}")
                            
                            # Check if this is our response
                            if message.get("id") == request_id:
                                return message
                                
                        except json.JSONDecodeError:
                            print(f"⚠️ Invalid JSON in SSE data: {data}")
                            continue
                            
            raise Exception("SSE stream ended without receiving response")
            
        except Exception as e:
            raise Exception(f"SSE processing failed: {str(e)}")              
    
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
        Download a specific attachment from Outlook using Composio MCP with search parameters
        """
        try:
            print(f"🔍 Starting Outlook attachment download via Composio MCP...")
            print(f"📋 Search params: subject='{email_subject}', attachment='{attachment_name}', sender='{sender_email}', days_back={days_back}")
            
            # Step 1: Initialize MCP connection
            init_response = await self._send_mcp_request("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "outlook-mcp-client",
                    "version": "1.0.0"
                }
            })
            print(f"🔗 MCP Initialize: {init_response}")
            
            # Step 2: Get available tools from the MCP server
            tools_response = await self._send_mcp_request("tools/list", {})
            print(f"📋 Available tools response: {tools_response}")
            
            # Step 3: Find Outlook/Email tools
            outlook_tools = []
            if "result" in tools_response and "tools" in tools_response["result"]:
                for tool in tools_response["result"]["tools"]:
                    tool_name = tool.get("name", "").lower()
                    if any(keyword in tool_name for keyword in ["outlook", "email", "attachment", "download", "search"]):
                        outlook_tools.append(tool)
                        print(f"📧 Found relevant tool: {tool['name']} - {tool.get('description', 'No description')}")
            
            if not outlook_tools:
                # Fallback: try common Outlook tool names
                common_tools = [
                    "outlook_download_attachment",
                    "outlook_search_emails",
                    "email_search",
                    "download_attachment",
                    "search_outlook"
                ]
                
                for tool_name in common_tools:
                    try:
                        # Test if tool exists by attempting to call it
                        test_response = await self._send_mcp_request("tools/call", {
                            "name": tool_name,
                            "arguments": {"test": True}
                        })
                        outlook_tools.append({"name": tool_name, "description": "Auto-detected tool"})
                        print(f"✅ Found working tool: {tool_name}")
                        break
                    except Exception:
                        continue
            
            if not outlook_tools:
                raise Exception("No Outlook tools found in MCP server. Available tools might use different naming.")
            
            # Step 4: Use the best available tool for attachment download
            selected_tool = outlook_tools[0]
            print(f"🛠️ Using tool: {selected_tool['name']}")
            
            # Step 5: Prepare comprehensive search parameters with flexible mapping
            search_params = {}
            
            # Enhanced parameter mapping for Composio MCP tools
            # Handle sender email with flexible formats
            if sender_email:
                # Support formats like "from:CustomerService@solarwinds.com"
                if sender_email.startswith("from:"):
                    sender_clean = sender_email[5:]  # Remove "from:" prefix
                else:
                    sender_clean = sender_email
                
                search_params["sender"] = sender_clean
                search_params["from"] = sender_clean
                search_params["sender_email"] = sender_clean
                search_params["from_email"] = sender_clean
            
            # Handle email subject
            if email_subject:
                search_params["subject"] = email_subject
                search_params["email_subject"] = email_subject
                search_params["query"] = email_subject
            
            # Handle attachment filename with multiple parameter names
            # Always provide file_name parameter (required by Composio MCP)
            filename_to_use = attachment_name or "attachment.pdf"  # Default filename if none provided
            search_params["filename"] = filename_to_use  # Primary parameter expected by tool
            search_params["file_name"] = filename_to_use  # Alternative parameter name (REQUIRED)
            search_params["attachment_name"] = filename_to_use
            search_params["attachment_filename"] = filename_to_use
            
            # Handle attachment ID with flexible formats
            if attachment_id:
                # Support dynamic references like {attachmentList[0][attachmentId]}
                if attachment_id.startswith("{") and attachment_id.endswith("}"):
                    # Handle dynamic reference - for now, use the raw ID
                    search_params["attachment_id"] = attachment_id
                    search_params["attachmentId"] = attachment_id
                else:
                    search_params["attachment_id"] = attachment_id
                    search_params["attachmentId"] = attachment_id
                    search_params["id"] = attachment_id
            
            # Handle message ID with flexible formats
            if message_id:
                # Support dynamic references like {messageId}
                if message_id.startswith("{") and message_id.endswith("}"):
                    # Handle dynamic reference - for now, use the raw ID
                    search_params["message_id"] = message_id
                    search_params["messageId"] = message_id
                else:
                    search_params["message_id"] = message_id
                    search_params["messageId"] = message_id
                    search_params["mail_id"] = message_id
            
            # Add time constraints and operational parameters
            search_params["days_back"] = days_back
            search_params["limit"] = 10  # Limit results for performance
            
            # Add action specification for the tool
            search_params["action"] = "download"
            search_params["operation"] = "download_attachment"
            search_params["task"] = "download_attachment"
            
            # Add additional context parameters that might be expected
            search_params["include_attachments"] = True
            search_params["download_content"] = True
            
            print(f"📤 Calling tool with params: {json.dumps(search_params, indent=2)}")
            
            # Step 6: Call the tool to download attachment
            tool_response = await self._send_mcp_request("tools/call", {
                "name": selected_tool["name"],
                "arguments": search_params
            })
            
            print(f"📥 Tool response: {json.dumps(tool_response, indent=2)}")
            
            # Step 7: Process and return results
            if "result" in tool_response:
                result_data = tool_response["result"]
                
                return {
                    "status": "success",
                    "message": "Attachment download completed via Composio MCP",
                    "mcp_server": self.mcp_endpoint,
                    "tool_used": selected_tool["name"],
                    "search_params": search_params,
                    "result": result_data,
                    "available_tools": [tool["name"] for tool in outlook_tools],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Handle error response
                error_info = tool_response.get("error", {"message": "Unknown error"})
                return {
                    "status": "error",
                    "message": f"Tool execution failed: {error_info.get('message', 'Unknown error')}",
                    "tool_used": selected_tool["name"],
                    "search_params": search_params,
                    "error": error_info,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            print(f"❌ Composio MCP download failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to download attachment via Composio MCP: {str(e)}",
                "error_details": str(e),
                "mcp_endpoint": self.mcp_endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def list_emails(
        self,
        email_subject: Optional[str] = None,
        sender_email: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        List emails matching criteria using Composio MCP via SSE
        
        Args:
            email_subject: Subject filter (optional)
            sender_email: Sender filter (optional)
            days_back: Number of days to look back (default: 7)
            
        Returns:
            Dict containing list of matching emails
        """
        try:
            since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # First, list available tools
            tools_response = await self._send_mcp_request("tools/list", {})
            
            if "error" in tools_response:
                raise Exception(f"Failed to list tools: {tools_response['error']['message']}")
            
            tools = tools_response.get("result", {}).get("tools", [])
            
            # Find Outlook-related tools for listing emails
            outlook_tools = [tool for tool in tools if 'outlook' in tool.get('name', '').lower()]
            
            if not outlook_tools:
                raise Exception("No Outlook tools found in MCP server")
            
            # Try to find the list emails tool
            list_tool = None
            for tool in outlook_tools:
                tool_name = tool.get('name', '').lower()
                if 'list' in tool_name or 'search' in tool_name:
                    list_tool = tool
                    break
            
            if not list_tool:
                # Use the first available Outlook tool
                list_tool = outlook_tools[0]
            
            # Call the tool with our parameters
            tool_response = await self._send_mcp_request(
                "tools/call",
                {
                    "name": list_tool["name"],
                    "arguments": {
                        "email_subject": email_subject,
                        "sender_email": sender_email,
                        "days_back": days_back,
                        "since_date": since_date
                    }
                }
            )
            
            if "error" in tool_response:
                raise Exception(f"Tool execution failed: {tool_response['error']['message']}")
            
            return {
                "tool_used": list_tool["name"],
                "result": tool_response.get("result", {}),
                "success": True
            }
                    
        except Exception as e:
            raise Exception(f"Failed to list emails via Composio MCP: {str(e)}")
