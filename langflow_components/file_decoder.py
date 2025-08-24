import base64
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
import json

from langflow.custom import Component
from langflow.io import Output, MessageTextInput, BoolInput, StrInput
from langflow.schema import Data


class FileDecoder(Component):
    """
    Langflow Custom Component: File Decoder
    
    Decodes base64 file content from API response and saves to disk.
    """
    
    display_name = "File Decoder"
    description = "Decode base64 file content and save to disk"
    icon = "file-down"
    name = "FileDecoder"
    
    inputs = [
        MessageTextInput(
            name="api_response",
            display_name="API Response",
            info="API response containing base64 file content",
        ),
        StrInput(
            name="output_directory",
            display_name="Output Directory",
            info="Directory to save decoded files (optional, uses temp if empty)",
            value="",
        ),
        BoolInput(
            name="preserve_filename",
            display_name="Preserve Filename",
            info="Use original filename from API response",
            value=True,
        ),
    ]
    
    outputs = [
        Output(display_name="File Info", name="file_info", method="decode_file"),
    ]

    def decode_file(self) -> Data:
        """Decode base64 file content and save to disk."""
        
        try:
            if not self.api_response:
                return Data(data={"error": "No API response provided"})
            
            # Parse API response
            if isinstance(self.api_response, str):
                try:
                    response_data = json.loads(self.api_response)
                except json.JSONDecodeError:
                    return Data(data={"error": "Invalid JSON in API response"})
            else:
                response_data = self.api_response
            
            # Extract file information from API response
            if "result" in response_data:
                file_data = response_data["result"]
            else:
                file_data = response_data
            
            # Get file details
            filename = file_data.get("filename", "downloaded_file")
            content_type = file_data.get("content_type", "application/octet-stream")
            size = file_data.get("size", 0)
            content_base64 = file_data.get("content_base64", "")
            
            if not content_base64:
                return Data(data={"error": "No base64 content found in response"})
            
            # Decode base64 content
            try:
                decoded_content = base64.b64decode(content_base64)
            except Exception as e:
                return Data(data={"error": f"Failed to decode base64 content: {str(e)}"})
            
            # Determine output path
            if self.output_directory and self.output_directory.strip():
                output_dir = Path(self.output_directory.strip())
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.gettempdir()) / "langflow_downloads"
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            if self.preserve_filename and filename:
                file_path = output_dir / filename
            else:
                # Generate unique filename
                import time
                timestamp = int(time.time())
                extension = Path(filename).suffix if filename else ".bin"
                file_path = output_dir / f"download_{timestamp}{extension}"
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(decoded_content)
            
            return Data(data={
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "original_filename": filename,
                "content_type": content_type,
                "size": size,
                "decoded_size": len(decoded_content),
                "output_directory": str(output_dir),
                "file_exists": file_path.exists(),
            })
            
        except Exception as e:
            return Data(data={
                "error": f"Error decoding file: {str(e)}",
                "success": False
            })
