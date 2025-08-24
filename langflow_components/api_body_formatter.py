from typing import Any, Dict
import json

from langflow.custom import Component
from langflow.io import Output, MessageTextInput
from langflow.schema import Data


class APIBodyFormatter(Component):
    """
    Langflow Custom Component: API Body Formatter
    
    Formats JSON data specifically for API Request component body input.
    Returns the raw dictionary that API Request can process directly.
    """
    
    display_name = "API Body Formatter"
    description = "Format JSON data for API Request body input"
    icon = "settings"
    name = "APIBodyFormatter"
    
    inputs = [
        MessageTextInput(
            name="json_input",
            display_name="JSON Input",
            info="JSON data to format for API request body",
        ),
    ]
    
    outputs = [
        Output(display_name="Formatted Body", name="formatted_body", method="format_body"),
    ]

    def format_body(self) -> Data:
        """Format JSON data for API Request body."""
        
        try:
            if not self.json_input:
                return Data(data={})
            
            # Parse the input data
            if isinstance(self.json_input, str):
                try:
                    parsed_data = json.loads(self.json_input)
                except json.JSONDecodeError:
                    # If not valid JSON, return as single field
                    return Data(data={"data": self.json_input})
            else:
                parsed_data = self.json_input
            
            # The API Request component's _process_body method expects the data
            # to be directly accessible. Return the parsed JSON structure directly.
            if isinstance(parsed_data, dict):
                return Data(data=parsed_data)
            else:
                return Data(data={"value": parsed_data})
            
        except Exception as e:
            return Data(data={
                "error": f"Error formatting body: {str(e)}"
            })
