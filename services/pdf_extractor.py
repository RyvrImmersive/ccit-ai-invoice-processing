"""
PDF Data Extraction Service for Outlook Attachments
Extracts structured data from PDF attachments before sending to Langflow
"""

import os
import json
import base64
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

# PDF processing libraries (install with: pip install PyPDF2 pdfplumber)
try:
    import PyPDF2
    import pdfplumber
    PDF_LIBRARIES_AVAILABLE = True
except ImportError:
    PDF_LIBRARIES_AVAILABLE = False
    print("⚠️ PDF libraries not installed. Install with: pip install PyPDF2 pdfplumber")

class PDFExtractor:
    """
    AI-powered PDF data extraction service
    Extracts structured data from PDF attachments for Langflow processing
    """
    
    def __init__(self):
        self.supported_formats = ['pdf']
        self.extraction_patterns = {
            'invoice': {
                'invoice_number': [
                    r'invoice\s*#?\s*:?\s*([A-Z0-9_-]+)',
                    r'inv\s*#?\s*:?\s*([A-Z0-9_-]+)',
                    r'bill\s*#?\s*:?\s*([A-Z0-9_-]+)'
                ],
                'amount': [
                    r'total\s*:?\s*\$?([0-9,]+\.?[0-9]*)',
                    r'amount\s*:?\s*\$?([0-9,]+\.?[0-9]*)',
                    r'due\s*:?\s*\$?([0-9,]+\.?[0-9]*)'
                ],
                'date': [
                    r'date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                    r'invoice\s*date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                    r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
                ],
                'vendor': [
                    r'from\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
                    r'bill\s*from\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
                    r'vendor\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)'
                ]
            },
            'receipt': {
                'merchant': [
                    r'([A-Za-z\s&.,]+?)(?:\n.*address|$)',
                    r'store\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)'
                ],
                'total': [
                    r'total\s*:?\s*\$?([0-9,]+\.?[0-9]*)',
                    r'amount\s*:?\s*\$?([0-9,]+\.?[0-9]*)'
                ],
                'date': [
                    r'date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                    r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
                ]
            }
        }
    
    async def extract_pdf_data(
        self, 
        pdf_content: bytes, 
        filename: str = None,
        extraction_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Extract structured data from PDF content
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for context
            extraction_type: 'auto', 'invoice', 'receipt', or 'general'
        
        Returns:
            Dict containing extracted structured data
        """
        if not PDF_LIBRARIES_AVAILABLE:
            return self._fallback_extraction(pdf_content, filename)
        
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            # Extract text using multiple methods
            text_content = await self._extract_text_content(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Determine document type if auto
            if extraction_type == 'auto':
                extraction_type = self._detect_document_type(text_content, filename)
            
            # Extract structured data based on type
            structured_data = await self._extract_structured_data(
                text_content, 
                extraction_type, 
                filename
            )
            
            return {
                'extraction_status': 'success',
                'document_type': extraction_type,
                'filename': filename,
                'extracted_data': structured_data,
                'raw_text': text_content[:1000] + '...' if len(text_content) > 1000 else text_content,
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'text_length': len(text_content),
                'confidence_score': self._calculate_confidence(structured_data)
            }
            
        except Exception as e:
            print(f"❌ PDF extraction error: {str(e)}")
            return self._fallback_extraction(pdf_content, filename, error=str(e))
    
    async def _extract_text_content(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods for better accuracy"""
        text_content = ""
        
        # Method 1: pdfplumber (better for structured documents)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            print(f"⚠️ pdfplumber extraction failed: {e}")
        
        # Method 2: PyPDF2 (fallback)
        if not text_content.strip():
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
            except Exception as e:
                print(f"⚠️ PyPDF2 extraction failed: {e}")
        
        return text_content.strip()
    
    def _detect_document_type(self, text: str, filename: str = None) -> str:
        """Detect document type based on content and filename"""
        text_lower = text.lower()
        filename_lower = (filename or "").lower()
        
        # Check for invoice indicators
        invoice_keywords = ['invoice', 'bill', 'payment due', 'amount due', 'inv#']
        if any(keyword in text_lower or keyword in filename_lower for keyword in invoice_keywords):
            return 'invoice'
        
        # Check for receipt indicators
        receipt_keywords = ['receipt', 'purchase', 'transaction', 'store', 'merchant']
        if any(keyword in text_lower or keyword in filename_lower for keyword in receipt_keywords):
            return 'receipt'
        
        return 'general'
    
    async def _extract_structured_data(
        self, 
        text: str, 
        doc_type: str, 
        filename: str
    ) -> Dict[str, Any]:
        """Extract structured data based on document type"""
        extracted_data = {
            'document_type': doc_type,
            'filename': filename,
            'extraction_method': 'pattern_matching'
        }
        
        if doc_type in self.extraction_patterns:
            patterns = self.extraction_patterns[doc_type]
            
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        extracted_data[field] = match.group(1).strip()
                        break
        
        # Add general metadata
        extracted_data.update({
            'word_count': len(text.split()),
            'character_count': len(text),
            'contains_numbers': bool(re.search(r'\d', text)),
            'contains_currency': bool(re.search(r'[\$€£¥]', text)),
            'contains_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text))
        })
        
        return extracted_data
    
    def _calculate_confidence(self, structured_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality"""
        score = 0.0
        max_score = 100.0
        
        # Base score for successful extraction
        score += 20.0
        
        # Points for specific field extraction
        key_fields = ['invoice_number', 'amount', 'total', 'date', 'vendor', 'merchant']
        extracted_fields = sum(1 for field in key_fields if field in structured_data and structured_data[field])
        score += (extracted_fields / len(key_fields)) * 60.0
        
        # Points for data quality indicators
        if structured_data.get('contains_numbers'):
            score += 10.0
        if structured_data.get('contains_currency'):
            score += 10.0
        
        return min(score, max_score)
    
    def _fallback_extraction(
        self, 
        pdf_content: bytes, 
        filename: str = None, 
        error: str = None
    ) -> Dict[str, Any]:
        """Fallback extraction when PDF libraries are not available"""
        return {
            'extraction_status': 'fallback',
            'document_type': 'unknown',
            'filename': filename,
            'extracted_data': {
                'file_size': len(pdf_content),
                'file_type': 'pdf',
                'filename': filename,
                'extraction_method': 'metadata_only'
            },
            'raw_text': f"PDF content available ({len(pdf_content)} bytes) but extraction libraries not installed",
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'error': error,
            'recommendation': 'Install PDF processing libraries: pip install PyPDF2 pdfplumber'
        }

    async def process_outlook_attachment(
        self, 
        attachment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process Outlook attachment data and extract PDF content if available
        
        Args:
            attachment_data: Response from Composio MCP attachment download
        
        Returns:
            Enhanced data with PDF extraction results
        """
        result = {
            'original_response': attachment_data,
            'pdf_extraction': None,
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        # Check if we have PDF content in the response
        if 'result' in attachment_data and 'content' in attachment_data['result']:
            content_items = attachment_data['result']['content']
            
            for item in content_items:
                if item.get('type') == 'text':
                    # Try to find base64 encoded PDF content
                    text_content = item.get('text', '')
                    
                    # Look for base64 PDF content
                    if 'base64' in text_content.lower() or text_content.startswith('JVBERi'):
                        try:
                            # Decode base64 PDF content
                            pdf_bytes = base64.b64decode(text_content)
                            
                            # Extract filename from search params
                            filename = attachment_data.get('search_params', {}).get('filename', 'attachment.pdf')
                            
                            # Extract structured data from PDF
                            pdf_extraction = await self.extract_pdf_data(pdf_bytes, filename)
                            result['pdf_extraction'] = pdf_extraction
                            
                        except Exception as e:
                            result['pdf_extraction'] = {
                                'extraction_status': 'error',
                                'error': str(e),
                                'message': 'Failed to decode or process PDF content'
                            }
        
        # If no PDF content found, create metadata-only result
        if not result['pdf_extraction']:
            result['pdf_extraction'] = {
                'extraction_status': 'no_pdf_content',
                'message': 'No PDF binary content found in Composio MCP response',
                'available_data': {
                    'filename': attachment_data.get('search_params', {}).get('filename'),
                    'attachment_id': attachment_data.get('search_params', {}).get('attachment_id'),
                    'message_id': attachment_data.get('search_params', {}).get('message_id'),
                    'sender': attachment_data.get('search_params', {}).get('sender')
                }
            }
        
        return result
