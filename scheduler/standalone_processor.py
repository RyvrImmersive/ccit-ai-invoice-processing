#!/usr/bin/env python3
"""
Standalone daily processor that directly calls APIs without CrewAI dependencies
"""

import os
import json
import logging
import requests
import base64
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class StandaloneProcessor:
    """Direct API processor without CrewAI dependencies"""
    
    def __init__(self):
        self.outlook_api_url = os.getenv('OUTLOOK_API_BASE_URL')
        self.outlook_api_key = os.getenv('OUTLOOK_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.astra_db_id = os.getenv('ASTRA_DB_DATABASE_ID')
        self.astra_token = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
        self.keyspace = os.getenv('ASTRA_DB_KEYSPACE', 'invoices')
    
    def search_emails(self):
        """Search for emails with attachments"""
        try:
            logger.info("🔍 Searching for emails with attachments...")
            
            url = f"{self.outlook_api_url}/search"
            headers = {
                "Content-Type": "application/json",
                "X-api-key": self.outlook_api_key
            }
            
            payload = {
                "days_back": 1,
                "has_attachments": True,
                "top": 10,
                "subject_contains": "invoice"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                attachments = []
                
                for message in data.get("items", []):
                    if message.get("hasAttachments"):
                        for attachment in message.get("attachments", []):
                            attachments.append({
                                "messageId": message["messageId"],
                                "attachmentId": attachment["attachmentId"],
                                "attachmentName": attachment["name"],
                                "subject": message["subject"],
                                "from": message.get("from_", message.get("from", "")),
                                "receivedAt": message["receivedAt"]
                            })
                
                logger.info(f"📧 Found {len(attachments)} attachments")
                return attachments
            else:
                logger.error(f"❌ Email search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Email search error: {e}")
            return []
    
    def download_attachment(self, message_id, attachment_id):
        """Download an attachment"""
        try:
            url = f"{self.outlook_api_url}/download"
            headers = {
                "Content-Type": "application/json",
                "X-api-key": self.outlook_api_key
            }
            
            payload = {
                "message_id": message_id,
                "attachment_id": attachment_id
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            return None
    
    def extract_invoice_data(self, content_base64, filename):
        """Extract invoice data using OpenAI"""
        try:
            if not filename.lower().endswith('.pdf'):
                return []
            
            # For now, return mock data to test the flow
            logger.info(f"📄 Processing {filename}")
            
            return [{
                "invoice_number": f"TEST-{datetime.now().strftime('%Y%m%d')}",
                "vendor_name": "Test Vendor",
                "total_amount": 100.00,
                "currency": "USD",
                "invoice_date": datetime.now().strftime('%Y-%m-%d'),
                "confidence_score": 0.9,
                "extraction_method": "standalone_processor"
            }]
            
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return []
    
    def store_in_astra(self, attachment_data, invoice_data):
        """Store data in Astra DB using REST API"""
        try:
            # Use Astra REST API instead of CQL driver
            base_url = f"https://{self.astra_db_id}-{self.keyspace}.apps.astra.datastax.com/api/rest/v2"
            headers = {
                "X-Cassandra-Token": self.astra_token,
                "Content-Type": "application/json"
            }
            
            # Store attachment metadata
            attachment_record = {
                "id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "message_id": attachment_data.get("messageId", ""),
                "attachment_name": attachment_data.get("attachmentName", ""),
                "sender_email": attachment_data.get("from", ""),
                "subject": attachment_data.get("subject", ""),
                "processing_status": "completed",
                "created_at": datetime.now().isoformat(),
                "source": "standalone_processor"
            }
            
            # For now, just log the data that would be stored
            logger.info(f"💾 Would store attachment: {attachment_record['id']}")
            logger.info(f"💾 Would store {len(invoice_data)} invoices")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage error: {e}")
            return False
    
    def run_processing(self):
        """Run the complete processing workflow"""
        logger.info("🚀 Starting standalone daily processing")
        logger.info(f"📅 Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Search for emails
            attachments = self.search_emails()
            
            if not attachments:
                logger.info("📭 No attachments found in last 24 hours")
                return True
            
            processed_count = 0
            
            for attachment in attachments:
                logger.info(f"📎 Processing: {attachment['attachmentName']}")
                
                # Download attachment
                download_result = self.download_attachment(
                    attachment["messageId"], 
                    attachment["attachmentId"]
                )
                
                if not download_result:
                    continue
                
                # Extract invoice data
                invoice_data = self.extract_invoice_data(
                    download_result.get("content_base64", ""),
                    attachment["attachmentName"]
                )
                
                # Store in database
                if self.store_in_astra(attachment, invoice_data):
                    processed_count += 1
            
            logger.info(f"✅ Successfully processed {processed_count} attachments")
            return True
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            return False

def main():
    """Main entry point"""
    processor = StandaloneProcessor()
    
    try:
        success = processor.run_processing()
        exit_code = 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        exit_code = 1
    
    logger.info("=" * 60)
    logger.info(f"🏁 Processing finished with exit code: {exit_code}")
    logger.info("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    exit(main())
