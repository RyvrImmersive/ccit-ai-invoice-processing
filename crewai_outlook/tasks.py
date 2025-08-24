from crewai import Task
from agents import (
    email_search_agent,
    attachment_download_agent, 
    data_extraction_agent,
    astra_db_agent,
    invoice_data_agent,
    monitoring_agent
)

# Task 1: Search emails and identify attachments
search_task = Task(
    description="""Search Outlook emails from the specified sender email address.
    
    Requirements:
    - Search for emails from sender: {sender_email}
    - Look for emails containing subject: {subject_contains} (if provided)
    - Search within the last {days_back} days
    - Focus only on emails that have attachments
    - Extract and return messageId, attachmentId, attachmentName for each attachment found
    - Provide comprehensive metadata including file sizes, content types, and email details
    
    Expected Output: JSON structure containing all found attachments with their metadata""",
    agent=email_search_agent,
    expected_output="JSON with attachment details including messageId, attachmentId, attachmentName, and metadata"
)

# Task 2: Download attachments
download_task = Task(
    description="""Download all attachments identified in the search results.
    
    Requirements:
    - Use the messageId and attachmentId from the search results
    - Download each attachment found in the previous task
    - Ensure all downloads are successful and complete
    - Return the downloaded file content in base64 format along with file metadata
    - Handle any download errors gracefully and report them
    
    Expected Output: JSON structure with downloaded attachment data including base64 content""",
    agent=attachment_download_agent,
    expected_output="JSON with downloaded attachment data including filename, content_type, size, and base64 content",
    context=[search_task]
)

# Task 3: Extract data from attachments
data_extraction_task = Task(
    description="""Extract meaningful data from the downloaded attachments and structure it into JSON.
    
    Requirements:
    - Process each downloaded attachment based on its content type
    - For PDF files: extract text content and metadata
    - For text files: extract and structure the text content
    - For JSON files: parse and validate the JSON structure
    - For other file types: provide basic file information and any extractable data
    - Structure all extracted data into a clean, consistent JSON format
    - Include extraction metadata and processing details
    
    Expected Output: Structured JSON containing all extracted data from attachments""",
    agent=data_extraction_agent,
    expected_output="Structured JSON with extracted data from all processed attachments",
    context=[download_task]
)

# Task 4: Store attachment metadata in Astra DB
storage_task = Task(
    description="""Store the extracted attachment metadata in Astra DB invoice_attachments table.
    
    Requirements:
    - Take the extracted data from the previous task
    - Store attachment metadata in the invoice_attachments table
    - Include all metadata: message ID, attachment name, sender, subject, timestamps
    - Ensure data integrity and proper formatting
    - Return confirmation with the attachment record ID for audit trail
    
    Expected Output: JSON confirmation of successful metadata storage with attachment record ID.""",
    expected_output="JSON object confirming successful storage in Astra DB with attachment record ID",
    agent=astra_db_agent,
    context=[data_extraction_task]
)

# Task 5: Store structured invoice data with audit trail
invoice_storage_task = Task(
    description="""Store structured invoice data in Astra DB invoice_data table with audit trail.
    
    Requirements:
    - Extract structured invoice fields from the data extraction results
    - Handle multiple invoices per attachment (up to 2 invoices)
    - Store each invoice separately in the invoice_data table
    - Link to the attachment record using attachment_record_id for audit trail
    - Include extraction timestamp and confidence scores
    - Return confirmation of all stored invoices
    
    Expected Output: JSON confirmation of successful structured data storage with invoice details.""",
    expected_output="JSON object confirming successful storage of structured invoice data with record IDs",
    agent=invoice_data_agent,
    context=[storage_task]
)

# Task 6: Monitor and report workflow status
monitoring_task = Task(
    description="""Monitor the entire invoice processing workflow and provide comprehensive status report.
    
    Requirements:
    - Review results from all previous tasks
    - Verify data integrity across both tables (invoice_attachments and invoice_data)
    - Check for any failures or incomplete processing
    - Provide summary of processed invoices with key metrics
    - Report any issues or recommendations for improvement
    
    Expected Output: Comprehensive workflow status report with processing summary.""",
    expected_output="Detailed status report of the complete invoice processing workflow",
    agent=monitoring_agent,
    context=[storage_task, invoice_storage_task]
)
