from typing import Any, Dict, List
import json
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from langflow.custom import Component
from langflow.io import Output, StrInput, SecretStrInput, MessageTextInput
from langflow.schema import Data
from langflow.field_typing import Tool


class EmailSearchInput(BaseModel):
    """Input schema for email search."""
    sender_email: str = Field(description="Email address of the sender to search for", default="")
    subject_contains: str = Field(description="Text that should be contained in the email subject", default="")
    days_back: int = Field(description="Number of days back to search", default=30)
    attachment_name: str = Field(description="Name of attachment to look for", default="")


class OutlookEmailTool(Component):
    """
    Langflow Custom Component: Outlook Email Search and Download Tool
    
    Creates a tool that agents can use to search emails and download attachments.
    """
    
    display_name = "Outlook Email Tool"
    description = "Tool for agents to search emails and download attachments"
    icon = "mail"
    name = "OutlookEmailTool"
    
    inputs = [
        MessageTextInput(
            name="input_data",
            display_name="Input Data",
            info="Input data from agent or previous component",
        ),
        StrInput(
            name="search_url",
            display_name="Search API URL",
            info="Outlook microservice search endpoint URL",
            value="https://outlook-microservice.onrender.com/search",
        ),
        StrInput(
            name="download_url",
            display_name="Download API URL", 
            info="Outlook microservice download endpoint URL",
            value="https://outlook-microservice.onrender.com/download",
        ),
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="API key for the Outlook microservice",
            value="",
        ),
    ]
    
    outputs = [
        Output(display_name="Tool", name="tool", method="create_tool"),
    ]

    def create_tool(self) -> Tool:
        """Create a StructuredTool for Langflow agents."""
        
        async def outlook_search_download(sender_email: str = "", subject_contains: str = "", days_back: int = 30, attachment_name: str = "") -> Dict[str, Any]:
            """Search for Outlook emails and download attachments."""
            return await self._async_search_download(sender_email, subject_contains, days_back, attachment_name)
        
        # Create the structured tool
        tool = StructuredTool.from_function(
            func=outlook_search_download,
            name="outlook_search_download",
            description="Search Outlook emails by sender, subject, or attachment name and download attachments. Use sender_email, subject_contains, days_back, and attachment_name as parameters.",
            args_schema=EmailSearchInput,
        )
        
        return tool

    async def _async_search_download(self, sender_email: str, subject_contains: str, days_back: int, attachment_name: str) -> Dict[str, Any]:
        """Internal async method to search and download."""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-api-key": self.api_key or "",
            }
            
            # Search for emails
            search_body = {
                "sender_email": sender_email,
                "subject_contains": subject_contains, 
                "days_back": days_back,
                "has_attachments": True,
                "top": 10
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Search emails
                search_response = await client.post(
                    self.search_url,
                    json=search_body,
                    headers=headers
                )
                
                if search_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Search failed: {search_response.status_code} - {search_response.text}"
                    }
                
                search_result = search_response.json()
                messages = search_result.get("items", [])
                
                if not messages:
                    return {
                        "success": False,
                        "message": "No emails found matching the criteria"
                    }
                
                # Find matching attachments
                downloads = []
                for message in messages:
                    if not message.get("hasAttachments"):
                        continue
                        
                    for attachment in message.get("attachments", []):
                        attachment_match = True
                        if attachment_name:
                            attachment_match = attachment_name.lower() in attachment.get("name", "").lower()
                        
                        if attachment_match:
                            # Download this attachment
                            download_body = {
                                "message_id": message["messageId"],
                                "attachment_id": attachment["attachmentId"]
                            }
                            
                            download_response = await client.post(
                                self.download_url,
                                json=download_body,
                                headers=headers
                            )
                            
                            if download_response.status_code == 200:
                                download_result = download_response.json()
                                downloads.append({
                                    "success": True,
                                    "filename": download_result.get("filename", ""),
                                    "size": download_result.get("size", 0),
                                    "content_type": download_result.get("content_type", ""),
                                    "message_subject": message.get("subject", ""),
                                    "from": message.get("from_", "")
                                })
                            else:
                                downloads.append({
                                    "success": False,
                                    "filename": attachment.get("name", ""),
                                    "error": f"Download failed: {download_response.status_code}"
                                })
                
                return {
                    "success": True,
                    "downloads": downloads,
                    "total_found": len(downloads),
                    "message": f"Found and processed {len(downloads)} attachments"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in search and download: {str(e)}"
            }
