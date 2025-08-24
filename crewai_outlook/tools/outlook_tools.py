import os
import json
import httpx
from typing import Dict, Any, List
from pathlib import Path
from crewai_tools import BaseTool
from pydantic import BaseModel, Field


class OutlookSearchTool(BaseTool):
    name: str = "outlook_search"
    description: str = "Search Outlook emails from a specific sender and extract messageId, attachmentId, and attachmentName"
    
    def _run(self, sender_email: str, subject_contains: str = "", days_back: int = 30) -> str:
        """Search Outlook emails and return message and attachment information."""
        try:
            api_url = f"{os.getenv('OUTLOOK_API_BASE_URL')}/search"
            api_key = os.getenv('OUTLOOK_API_KEY')
            
            headers = {
                "Content-Type": "application/json",
                "X-api-key": api_key
            }
            
            payload = {
                "days_back": days_back,
                "has_attachments": True,
                "top": 10
            }
            
            # Only add sender_email if it's not empty
            if sender_email and sender_email.strip():
                payload["sender_email"] = sender_email
            
            # Only add subject_contains if it's not empty
            if subject_contains and subject_contains.strip():
                payload["subject_contains"] = subject_contains
            
            response = httpx.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("items", [])
                
                results = []
                for message in messages:
                    if message.get("hasAttachments"):
                        for attachment in message.get("attachments", []):
                            results.append({
                                "messageId": message["messageId"],
                                "attachmentId": attachment["attachmentId"],
                                "attachmentName": attachment["name"],
                                "attachmentSize": attachment["size"],
                                "contentType": attachment["contentType"],
                                "subject": message["subject"],
                                "from": message.get("from_", message.get("from", "")),
                                "receivedAt": message["receivedAt"]
                            })
                
                return json.dumps({
                    "success": True,
                    "attachments_found": len(results),
                    "attachments": results
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"API request failed: {response.status_code} - {response.text}"
                })
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Search failed: {str(e)}"
            })


class OutlookDownloadTool(BaseTool):
    name: str = "outlook_download"
    description: str = "Download Outlook attachment using messageId and attachmentId"
    
    def _run(self, message_id: str, attachment_id: str) -> str:
        """Download an Outlook attachment and return file information."""
        try:
            api_url = f"{os.getenv('OUTLOOK_API_BASE_URL')}/download"
            api_key = os.getenv('OUTLOOK_API_KEY')
            
            if not api_key:
                return json.dumps({
                    "success": False,
                    "error": "OUTLOOK_API_KEY not found in environment variables"
                })
            
            headers = {
                "Content-Type": "application/json",
                "X-api-key": api_key
            }
            
            payload = {
                "message_id": message_id,
                "attachment_id": attachment_id
            }
            
            response = httpx.post(api_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return json.dumps({
                    "success": True,
                    "filename": data.get("filename", "unknown"),
                    "content_type": data.get("content_type", "application/octet-stream"),
                    "size": data.get("size", 0),
                    "content": data.get("content_base64", "")
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Download failed: {response.status_code} - {response.text}"
                })
                
        except Exception as e:
            import traceback
            return json.dumps({
                "success": False,
                "error": f"Download failed: {str(e)}",
                "traceback": traceback.format_exc()
            })


class DataExtractionTool(BaseTool):
    name: str = "data_extraction"
    description: str = "Extract data from downloaded attachment files (PDF, text, JSON, etc.)"
    
    def _extract_invoice_fields(self, text_content: str) -> list:
        """Extract structured invoice fields from text using AI. Can handle multiple invoices (up to 2)."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""
            Analyze the following text and extract structured invoice data. The text may contain 1 or 2 invoices maximum.
            
            Return a JSON array where each element represents one invoice with these fields:
            - invoice_number: string
            - vendor_name: string
            - vendor_address: string
            - invoice_date: string (YYYY-MM-DD format)
            - due_date: string (YYYY-MM-DD format)
            - total_amount: number
            - currency: string (e.g., USD, EUR)
            - tax_amount: number
            - subtotal_amount: number
            - line_items: array of objects with description, quantity, unit_price, total
            - payment_terms: string
            - purchase_order_number: string
            - bill_to_name: string
            - bill_to_address: string
            - ship_to_name: string
            - ship_to_address: string
            - notes: string
            - invoice_sequence: number (1 for first invoice, 2 for second if present)
            
            If a field is not found, use null. Be precise with numbers and dates.
            If only one invoice is found, return an array with one element.
            If no clear invoice structure is found, return an empty array.
            
            Invoice Text:
            {text_content}
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            extracted_invoices = json.loads(response.choices[0].message.content)
            
            # Ensure it's a list and add metadata
            if not isinstance(extracted_invoices, list):
                extracted_invoices = [extracted_invoices] if extracted_invoices else []
            
            # Limit to maximum 2 invoices and add metadata
            extracted_invoices = extracted_invoices[:2]
            for i, invoice in enumerate(extracted_invoices):
                invoice["confidence_score"] = 0.9  # High confidence for GPT-4
                invoice["extraction_method"] = "openai_gpt4"
                invoice["invoice_sequence"] = i + 1
            
            return extracted_invoices
            
        except Exception as e:
            # Fallback to single invoice structure
            return [{
                "invoice_number": None,
                "vendor_name": None,
                "vendor_address": None,
                "invoice_date": None,
                "due_date": None,
                "total_amount": None,
                "currency": None,
                "tax_amount": None,
                "subtotal_amount": None,
                "line_items": [],
                "payment_terms": None,
                "purchase_order_number": None,
                "bill_to_name": None,
                "bill_to_address": None,
                "ship_to_name": None,
                "ship_to_address": None,
                "notes": f"Extraction failed: {str(e)}",
                "confidence_score": 0.1,
                "extraction_method": "fallback",
                "invoice_sequence": 1
            }]
    
    def _run(self, file_content: str, filename: str = "unknown") -> str:
        """Extract data from downloaded attachment content."""
        try:
            # Determine file type from filename extension
            file_ext = filename.lower().split('.')[-1] if '.' in filename else 'unknown'
            
            if file_ext == 'pdf':
                # Extract text from PDF
                import PyPDF2
                import io
                
                # Decode base64 content
                import base64
                pdf_data = base64.b64decode(file_content)
                
                # Read PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                # Extract structured invoice fields using AI (can handle multiple invoices)
                structured_invoices = self._extract_invoice_fields(text_content)
                
                return json.dumps({
                    "success": True,
                    "extracted_data": {
                        "filename": filename,
                        "content_type": "application/pdf",
                        "text_content": text_content,
                        "page_count": len(pdf_reader.pages),
                        "invoice_count": len(structured_invoices),
                        "structured_invoice_data": structured_invoices
                    }
                }, indent=2)
                
            elif file_ext in ['txt', 'csv']:
                # Handle text files
                import base64
                text_data = base64.b64decode(file_content).decode('utf-8')
                
                # Extract structured invoice fields if it looks like an invoice
                structured_invoices = self._extract_invoice_fields(text_data)
                
                return json.dumps({
                    "success": True,
                    "extracted_data": {
                        "filename": filename,
                        "content_type": "text/plain",
                        "text_content": text_data,
                        "invoice_count": len(structured_invoices),
                        "structured_invoice_data": structured_invoices
                    }
                }, indent=2)
                
            elif file_ext == 'json':
                # Handle JSON files
                import base64
                json_data = base64.b64decode(file_content).decode('utf-8')
                parsed_json = json.loads(json_data)
                
                return json.dumps({
                    "success": True,
                    "extracted_data": {
                        "filename": filename,
                        "content_type": "application/json",
                        "json_content": parsed_json
                    }
                }, indent=2)
                
            else:
                # Unknown file type - return basic info
                return json.dumps({
                    "success": True,
                    "extracted_data": {
                        "filename": filename,
                        "content_type": "unknown",
                        "message": f"Unsupported file type: {file_ext}",
                        "raw_content_length": len(file_content)
                    }
                }, indent=2)
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Data extraction failed: {str(e)}"
            })
    
    def _extract_pdf_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from PDF file."""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", "")
                    }
                
                return {
                    "content_type": "pdf",
                    "page_count": len(pdf_reader.pages),
                    "text_content": text_content.strip(),
                    "metadata": metadata,
                    "extraction_method": "PyPDF2"
                }
        except Exception as e:
            return {
                "content_type": "pdf",
                "error": f"PDF extraction failed: {str(e)}",
                "extraction_method": "PyPDF2"
            }
    
    def _extract_text_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return {
                "content_type": "text",
                "text_content": content,
                "character_count": len(content),
                "line_count": len(content.split('\n')),
                "extraction_method": "text_reader"
            }
        except Exception as e:
            return {
                "content_type": "text",
                "error": f"Text extraction failed: {str(e)}",
                "extraction_method": "text_reader"
            }
    
    def _extract_json_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            return {
                "content_type": "json",
                "json_data": json_data,
                "extraction_method": "json_parser"
            }
        except Exception as e:
            return {
                "content_type": "json",
                "error": f"JSON extraction failed: {str(e)}",
                "extraction_method": "json_parser"
            }


class InvoiceDataStorageTool(BaseTool):
    name: str = "invoice_data_storage"
    description: str = "Store structured invoice data in Astra DB invoice_data table with audit trail"
    
    def _run(self, structured_invoice_data: str, attachment_record_id: str) -> str:
        """Store structured invoice data in Astra DB invoice_data table. Handles multiple invoices per attachment."""
        try:
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider
            from datetime import datetime
            import uuid
            import os
            import tempfile
            import requests
            from decimal import Decimal
            
            # Get Astra DB configuration
            database_id = os.getenv('ASTRA_DB_DATABASE_ID')
            token = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
            keyspace = os.getenv('ASTRA_DB_KEYSPACE', 'invoices')
            table_name = 'invoice_data'
            
            if not database_id or not token:
                return json.dumps({
                    "success": False,
                    "error": "Astra DB configuration missing. Please set ASTRA_DB_DATABASE_ID and ASTRA_DB_APPLICATION_TOKEN"
                })
            
            # Parse structured invoice data
            if isinstance(structured_invoice_data, str):
                try:
                    invoice_data = json.loads(structured_invoice_data)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON in structured_invoice_data"
                    })
            else:
                invoice_data = structured_invoice_data
            
            # Handle multiple invoices - extract from structured_invoice_data array
            invoices_to_store = []
            if isinstance(invoice_data, dict) and 'structured_invoice_data' in invoice_data:
                invoices_to_store = invoice_data['structured_invoice_data']
            elif isinstance(invoice_data, list):
                invoices_to_store = invoice_data
            else:
                invoices_to_store = [invoice_data]
            
            # Ensure we have a list and limit to 2 invoices
            if not isinstance(invoices_to_store, list):
                invoices_to_store = [invoices_to_store]
            invoices_to_store = invoices_to_store[:2]
            
            # Generate record ID and timestamps
            record_id = uuid.uuid4()
            extraction_timestamp = datetime.utcnow()
            created_timestamp = datetime.utcnow()
            
            # Download secure connect bundle
            bundle_url = f"https://api.astra.datastax.com/v2/databases/{database_id}/secureBundleURL"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            bundle_response = requests.post(bundle_url, headers=headers)
            if bundle_response.status_code != 200:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to get secure bundle: {bundle_response.status_code}"
                })
            
            bundle_download_url = bundle_response.json()["downloadURL"]
            bundle_data = requests.get(bundle_download_url).content
            
            # Save bundle to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as bundle_file:
                bundle_file.write(bundle_data)
                bundle_path = bundle_file.name
            
            # Connect to Astra DB
            auth_provider = PlainTextAuthProvider(username='token', password=token)
            cluster = Cluster(cloud={'secure_connect_bundle': bundle_path}, auth_provider=auth_provider)
            session = cluster.connect(keyspace)
            
            # Prepare CQL INSERT statement
            insert_query = f"""
            INSERT INTO {table_name} (
                id, attachment_record_id, message_id, attachment_name, invoice_number,
                vendor_name, vendor_address, invoice_date, due_date, total_amount,
                currency, tax_amount, subtotal_amount, line_items, payment_terms,
                purchase_order_number, bill_to_name, bill_to_address, ship_to_name,
                ship_to_address, notes, confidence_score, extraction_method,
                extraction_timestamp, created_at, updated_at, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            prepared = session.prepare(insert_query)
            
            # Convert data types for Cassandra
            def safe_decimal(value):
                if value is None:
                    return None
                try:
                    return Decimal(str(value))
                except:
                    return None
            
            def safe_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    return None
            
            # Store each invoice separately
            stored_invoices = []
            
            for invoice in invoices_to_store:
                individual_record_id = uuid.uuid4()
                
                # Execute insert for each invoice
                session.execute(prepared, [
                    individual_record_id,
                    uuid.UUID(attachment_record_id),
                    invoice.get('message_id', ''),
                    invoice.get('attachment_name', ''),
                    invoice.get('invoice_number'),
                    invoice.get('vendor_name'),
                    invoice.get('vendor_address'),
                    safe_date(invoice.get('invoice_date')),
                    safe_date(invoice.get('due_date')),
                    safe_decimal(invoice.get('total_amount')),
                    invoice.get('currency'),
                    safe_decimal(invoice.get('tax_amount')),
                    safe_decimal(invoice.get('subtotal_amount')),
                    json.dumps(invoice.get('line_items', [])),
                    invoice.get('payment_terms'),
                    invoice.get('purchase_order_number'),
                    invoice.get('bill_to_name'),
                    invoice.get('bill_to_address'),
                    invoice.get('ship_to_name'),
                    invoice.get('ship_to_address'),
                    invoice.get('notes'),
                    invoice.get('confidence_score', 0.0),
                    invoice.get('extraction_method', 'unknown'),
                    extraction_timestamp,
                    created_timestamp,
                    created_timestamp,
                    "crewai_outlook_processor"
                ])
                
                stored_invoices.append({
                    "record_id": str(individual_record_id),
                    "invoice_number": invoice.get('invoice_number'),
                    "vendor_name": invoice.get('vendor_name'),
                    "total_amount": invoice.get('total_amount'),
                    "invoice_sequence": invoice.get('invoice_sequence', 1)
                })
            
            # Clean up
            cluster.shutdown()
            os.unlink(bundle_path)
            
            return json.dumps({
                "success": True,
                "invoices_stored": len(stored_invoices),
                "attachment_record_id": attachment_record_id,
                "table": table_name,
                "keyspace": keyspace,
                "extraction_timestamp": extraction_timestamp.isoformat(),
                "message": f"Successfully stored {len(stored_invoices)} invoice(s) in Astra DB",
                "stored_invoices": stored_invoices
            }, indent=2, default=str)
            
        except ImportError:
            return json.dumps({
                "success": False,
                "error": "cassandra-driver library not installed. Run: pip install cassandra-driver"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Invoice data storage failed: {str(e)}"
            })


class AstraDBTool(BaseTool):
    name: str = "astra_db_storage"
    description: str = "Store extracted attachment metadata in Astra DB invoice_attachments table"
    
    def _run(self, extracted_data: str) -> str:
        """Store extracted data in Astra DB invoice_attachments table."""
        try:
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider
            from datetime import datetime
            import uuid
            import os
            
            # Get Astra DB configuration
            database_id = os.getenv('ASTRA_DB_DATABASE_ID')
            token = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
            keyspace = os.getenv('ASTRA_DB_KEYSPACE', 'invoices')
            table_name = os.getenv('ASTRA_DB_TABLE', 'invoice_attachments')
            
            if not database_id or not token:
                return json.dumps({
                    "success": False,
                    "error": "Astra DB configuration missing. Please set ASTRA_DB_DATABASE_ID and ASTRA_DB_APPLICATION_TOKEN"
                })
            
            # Parse extracted data if it's a string
            if isinstance(extracted_data, str):
                try:
                    data_payload = json.loads(extracted_data)
                except json.JSONDecodeError:
                    data_payload = {"raw_data": extracted_data}
            else:
                data_payload = extracted_data
            
            # Extract relevant fields from the data payload
            attachment_info = data_payload.get('extracted_data', {})
            filename = attachment_info.get('filename', 'unknown')
            
            # Generate record ID and timestamp
            record_id = uuid.uuid4()
            timestamp = datetime.utcnow()
            
            # Use cassandra-driver for CQL table insertion
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider
            from ssl import SSLContext, PROTOCOL_TLSv1_2, CERT_REQUIRED
            import tempfile
            import requests
            
            # Download secure connect bundle
            bundle_url = f"https://api.astra.datastax.com/v2/databases/{database_id}/secureBundleURL"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            bundle_response = requests.post(bundle_url, headers=headers)
            if bundle_response.status_code != 200:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to get secure bundle: {bundle_response.status_code} - {bundle_response.text}"
                })
            
            bundle_download_url = bundle_response.json()["downloadURL"]
            bundle_data = requests.get(bundle_download_url).content
            
            # Save bundle to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as bundle_file:
                bundle_file.write(bundle_data)
                bundle_path = bundle_file.name
            
            # Connect to Astra DB
            auth_provider = PlainTextAuthProvider(username='token', password=token)
            cluster = Cluster(cloud={'secure_connect_bundle': bundle_path}, auth_provider=auth_provider)
            session = cluster.connect(keyspace)
            
            # Prepare CQL INSERT statement
            insert_query = f"""
            INSERT INTO {table_name} (
                id, message_id, attachment_name, sender_email, subject, 
                received_at, extracted_data, content_type, file_size, 
                processing_status, created_at, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            prepared = session.prepare(insert_query)
            
            # Execute insert
            session.execute(prepared, [
                record_id,
                data_payload.get('messageId', ''),
                filename,
                data_payload.get('from', ''),
                data_payload.get('subject', ''),
                timestamp,
                json.dumps(data_payload),
                attachment_info.get('content_type', ''),
                attachment_info.get('size', 0),
                "completed",
                timestamp,
                "crewai_outlook_processor"
            ])
            
            # Clean up
            cluster.shutdown()
            os.unlink(bundle_path)
            
            return json.dumps({
                "success": True,
                "record_id": str(record_id),
                "table": table_name,
                "keyspace": keyspace,
                "timestamp": timestamp.isoformat(),
                "message": "Data successfully inserted into Astra DB"
            }, indent=2, default=str)
            
        except ImportError:
            return json.dumps({
                "success": False,
                "error": "cassandra-driver library not installed. Run: pip install cassandra-driver"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Astra DB storage preparation failed: {str(e)}"
            })
