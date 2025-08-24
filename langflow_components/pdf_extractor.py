import os
from pathlib import Path
from typing import Any, Dict

from langflow.custom import Component
from langflow.io import Output, MessageTextInput, BoolInput
from langflow.schema import Data


class PDFExtractor(Component):
    """
    Langflow Custom Component: PDF Text Extractor
    
    Extracts text content from PDF files using PyPDF2.
    """
    
    display_name = "PDF Text Extractor"
    description = "Extract text content from PDF files"
    icon = "file-text"
    name = "PDFExtractor"
    
    inputs = [
        MessageTextInput(
            name="file_info",
            display_name="File Info",
            info="File information from File Decoder component",
        ),
        BoolInput(
            name="extract_metadata",
            display_name="Extract Metadata",
            info="Extract PDF metadata along with text",
            value=True,
        ),
    ]
    
    outputs = [
        Output(display_name="Extracted Content", name="extracted_content", method="extract_pdf_text"),
    ]

    def extract_pdf_text(self) -> Data:
        """Extract text content from PDF file."""
        
        try:
            if not self.file_info:
                return Data(data={"error": "No file info provided"})
            
            # Parse file info
            import json
            if isinstance(self.file_info, str):
                try:
                    file_data = json.loads(self.file_info)
                except json.JSONDecodeError:
                    return Data(data={"error": "Invalid JSON in file info"})
            else:
                file_data = self.file_info
            
            # Get file path
            file_path = file_data.get("file_path", "")
            if not file_path:
                return Data(data={"error": "No file path found in file info"})
            
            file_path = Path(file_path)
            if not file_path.exists():
                return Data(data={"error": f"File not found: {file_path}"})
            
            # Check if it's a PDF
            content_type = file_data.get("content_type", "")
            if "pdf" not in content_type.lower() and not str(file_path).lower().endswith('.pdf'):
                return Data(data={"error": f"File is not a PDF: {content_type}"})
            
            # Extract text using PyPDF2
            try:
                import PyPDF2
            except ImportError:
                return Data(data={
                    "error": "PyPDF2 not installed. Install with: pip install PyPDF2",
                    "install_command": "pip install PyPDF2"
                })
            
            extracted_text = ""
            metadata = {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata if requested
                if self.extract_metadata:
                    if pdf_reader.metadata:
                        metadata = {
                            "title": pdf_reader.metadata.get("/Title", ""),
                            "author": pdf_reader.metadata.get("/Author", ""),
                            "subject": pdf_reader.metadata.get("/Subject", ""),
                            "creator": pdf_reader.metadata.get("/Creator", ""),
                            "producer": pdf_reader.metadata.get("/Producer", ""),
                            "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                            "modification_date": str(pdf_reader.metadata.get("/ModDate", "")),
                        }
                
                # Extract text from all pages
                num_pages = len(pdf_reader.pages)
                page_texts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        page_texts.append({
                            "page_number": page_num + 1,
                            "text": page_text,
                            "char_count": len(page_text)
                        })
                        extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        page_texts.append({
                            "page_number": page_num + 1,
                            "text": "",
                            "error": str(e),
                            "char_count": 0
                        })
            
            return Data(data={
                "success": True,
                "file_path": str(file_path),
                "filename": file_data.get("filename", ""),
                "extracted_text": extracted_text.strip(),
                "page_count": num_pages,
                "pages": page_texts,
                "metadata": metadata,
                "total_characters": len(extracted_text),
                "content_type": content_type,
                "extraction_method": "PyPDF2"
            })
            
        except Exception as e:
            return Data(data={
                "error": f"Error extracting PDF text: {str(e)}",
                "success": False
            })
