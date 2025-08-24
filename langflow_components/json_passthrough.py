from typing import Any, Dict
import json

from langflow.custom import Component
from langflow.io import Output, MessageTextInput
from langflow.schema import Data


class JSONPassthrough(Component):
    """
    Langflow Custom Component: JSON Passthrough for API Requests
    
    Receives JSON data from an agent and passes it through in the exact format
    needed for API requests (preserves original structure).
    """
    
    display_name = "JSON Passthrough"
    description = "Pass JSON data through for API requests without modification"
    icon = "arrow-right"
    name = "JSONPassthrough"
    
    inputs = [
        MessageTextInput(
            name="json_data",
            display_name="JSON Data",
            info="JSON data from another agent/component",
        ),
    ]
    
    outputs = [
        Output(display_name="JSON Output", name="json_output", method="pass_json"),
        Output(display_name="Body Format", name="body_format", method="get_body_format"),
    ]

    def pass_json(self) -> Data:
        """Pass JSON data through without modification."""
        
        try:
            if not self.json_data:
                return Data(data={})
            
            # Parse the input data
            if isinstance(self.json_data, str):
                try:
                    parsed_data = json.loads(self.json_data)
                except json.JSONDecodeError:
                    # If not valid JSON, return as-is
                    return Data(data={"raw_data": self.json_data})
            else:
                parsed_data = self.json_data
            
            # For API Request compatibility, return the parsed data directly
            # This ensures the API Request component gets the raw JSON structure
            if isinstance(parsed_data, dict):
                return Data(data=parsed_data)
            else:
                return Data(data={"data": parsed_data})
            
        except Exception as e:
            # Return error information
            return Data(data={
                "error": True,
                "message": f"Error processing JSON: {str(e)}",
                "original_data": str(self.json_data) if self.json_data else None
            })

    def get_body_format(self) -> Data:
        """Convert JSON data to API Request body format (list of key-value pairs)."""
        
        try:
            if not self.json_data:
                return Data(data={"body_list": []})
            
            # Parse the input data
            if isinstance(self.json_data, str):
                try:
                    parsed_data = json.loads(self.json_data)
                except json.JSONDecodeError:
                    return Data(data={"body_list": [{"key": "data", "value": self.json_data}]})
            else:
                parsed_data = self.json_data
            
            # Convert to list of key-value pairs for API Request body
            if isinstance(parsed_data, dict):
                body_list = [
                    {"key": k, "value": v} 
                    for k, v in parsed_data.items()
                ]
                return Data(data={"body_list": body_list})
            else:
                return Data(data={"body_list": [{"key": "data", "value": str(parsed_data)}]})
            
        except Exception as e:
            return Data(data={"body_list": [{
                "key": "error", 
                "value": f"Error processing JSON: {str(e)}"
            }]})
