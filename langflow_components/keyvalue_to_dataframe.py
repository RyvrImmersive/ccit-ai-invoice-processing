from typing import Any, Dict, List, Union
import pandas as pd
import json

from langflow.custom import Component
from langflow.io import Output, StrInput, BoolInput, MessageTextInput
from langflow.schema import Data


class KeyValueToDataFrame(Component):
    """
    Langflow Custom Component: Key-Value to DataFrame Converter
    
    Converts incoming key:value pairs into a clean pandas DataFrame
    without any additional characters, comments, or formatting.
    """
    
    display_name = "Key-Value to DataFrame"
    description = "Convert key:value pairs into a clean pandas DataFrame"
    icon = "table"
    name = "KeyValueToDataFrame"
    
    inputs = [
        MessageTextInput(
            name="agent_data",
            display_name="Agent Data",
            info="Data input from another agent/component",
        ),
        StrInput(
            name="input_data",
            display_name="Manual Input Data",
            info="Optional: Key-value pairs as JSON string, dictionary, or comma-separated pairs",
            value="",
        ),
        BoolInput(
            name="transpose",
            display_name="Transpose DataFrame",
            info="If True, keys become columns; if False, keys become rows",
            value=False,
        ),
        StrInput(
            name="key_column_name",
            display_name="Key Column Name",
            info="Name for the key column (when transpose=False)",
            value="key",
        ),
        StrInput(
            name="value_column_name", 
            display_name="Value Column Name",
            info="Name for the value column (when transpose=False)",
            value="value",
        ),
        BoolInput(
            name="api_format",
            display_name="API Format",
            info="If True, outputs original JSON structure for API requests instead of DataFrame",
            value=False,
        ),
    ]
    
    outputs = [
        Output(display_name="DataFrame", name="dataframe", method="convert_to_dataframe"),
    ]

    def convert_to_dataframe(self) -> Data:
        """Convert key-value pairs to DataFrame."""
        
        try:
            # Priority: agent_data > input_data
            data_to_process = None
            
            # Check for agent data first
            if self.agent_data:
                data_to_process = self.agent_data
            # Fallback to manual input
            elif self.input_data and self.input_data.strip():
                data_to_process = self.input_data.strip()
            
            if not data_to_process:
                # Return empty DataFrame
                df = pd.DataFrame()
                return Data(data={
                    "dataframe": df.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "empty": True
                })
            
            # Parse input data
            parsed_data = self._parse_input_data(data_to_process)
            
            if not parsed_data:
                # Return empty DataFrame if no valid data
                df = pd.DataFrame()
                return Data(data={
                    "dataframe": df.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "empty": True
                })
            
            # Check if API format is requested OR if data contains API-specific fields
            api_fields = ['message_id', 'attachment_id', 'email_subject', 'attachment_name']
            has_api_fields = any(field in parsed_data for field in api_fields)
            
            if self.api_format or has_api_fields:
                # Return original JSON structure for API requests
                return Data(data=parsed_data)
            
            # Create DataFrame based on transpose setting
            if self.transpose:
                # Keys become columns, single row with values
                df = pd.DataFrame([parsed_data])
            else:
                # Keys and values as separate columns
                key_col = self.key_column_name or "key"
                value_col = self.value_column_name or "value"
                
                df = pd.DataFrame([
                    {key_col: k, value_col: v} 
                    for k, v in parsed_data.items()
                ])
            
            # Convert DataFrame to clean dictionary format
            dataframe_dict = {
                "dataframe": df.to_dict('records'),
                "columns": df.columns.tolist(),
                "shape": df.shape,
                "dtypes": df.dtypes.astype(str).to_dict(),
                "empty": False
            }
            
            return Data(data=dataframe_dict)
            
        except Exception as e:
            # Return error information
            error_dict = {
                "error": True,
                "message": f"Error converting to DataFrame: {str(e)}",
                "dataframe": [],
                "columns": [],
                "shape": [0, 0],
                "empty": True
            }
            return Data(data=error_dict)

    def _parse_input_data(self, input_data: Any) -> Dict[str, Any]:
        """Parse various input formats into key-value dictionary."""
        
        # If input_data is already a dictionary, return it directly
        if isinstance(input_data, dict):
            return input_data
        
        # If input_data is a list, convert to dictionary
        if isinstance(input_data, list):
            result = {}
            for i, item in enumerate(input_data):
                if isinstance(item, dict):
                    for k, v in item.items():
                        result[f"{k}_{i}"] = v
                else:
                    result[f"item_{i}"] = item
            return result
        
        # Convert to string for parsing
        input_str = str(input_data)
        
        # Try JSON parsing first
        try:
            data = json.loads(input_str)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # Convert list of objects to flat dictionary
                result = {}
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            result[f"{k}_{i}"] = v
                    else:
                        result[f"item_{i}"] = item
                return result
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try comma-separated key:value pairs
        try:
            pairs = input_str.split(',')
            result = {}
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    
                    # Try to convert value to appropriate type
                    result[key] = self._convert_value(value)
                elif '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    
                    # Try to convert value to appropriate type
                    result[key] = self._convert_value(value)
            
            if result:
                return result
        except Exception:
            pass
        
        # Try line-separated key:value pairs
        try:
            lines = input_str.split('\n')
            result = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    result[key] = self._convert_value(value)
                elif '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    result[key] = self._convert_value(value)
            
            if result:
                return result
        except Exception:
            pass
        
        # If all parsing fails, treat as single key-value pair
        if ':' in input_str:
            key, value = input_str.split(':', 1)
            return {key.strip(): self._convert_value(value.strip())}
        elif '=' in input_str:
            key, value = input_str.split('=', 1)
            return {key.strip(): self._convert_value(value.strip())}
        
        # Last resort: treat entire string as a single value with generic key
        return {"data": input_str}

    def _convert_value(self, value_str: str) -> Any:
        """Convert string value to appropriate Python type."""
        
        # Remove quotes if present
        value_str = value_str.strip().strip('"\'')
        
        # Try boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        
        # Try integer
        try:
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Try None/null
        if value_str.lower() in ('none', 'null', ''):
            return None
        
        # Return as string
        return value_str
