import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from tools.outlook_tools import OutlookSearchTool, OutlookDownloadTool, DataExtractionTool, AstraDBTool, InvoiceDataStorageTool

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Agent 1: Email Search Agent
email_search_agent = Agent(
    role="Email Search Specialist",
    goal="Search Outlook emails from specific senders and identify attachments with their metadata",
    backstory="""You are an expert at searching through Outlook emails efficiently. 
    Your specialty is finding emails from specific senders and extracting detailed information 
    about their attachments including messageId, attachmentId, and attachment names. 
    You always provide comprehensive results with all necessary metadata for downstream processing.""",
    tools=[OutlookSearchTool()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
)

# Agent 2: Attachment Download Agent
attachment_download_agent = Agent(
    role="Attachment Download Specialist",
    goal="Download email attachments using messageId and attachmentId from search results",
    backstory="""You are a reliable attachment download specialist who takes messageId and 
    attachmentId information and efficiently downloads the corresponding attachments. 
    You handle various file types and ensure the downloaded content is properly encoded 
    and ready for further processing. You always verify successful downloads and provide 
    detailed file information.""",
    tools=[OutlookDownloadTool()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
)

# Agent 3: Data Extraction Agent
data_extraction_agent = Agent(
    role="Data Extraction Specialist",
    goal="Extract meaningful data from downloaded attachments and structure it into JSON format",
    backstory="""You are an expert data extraction specialist who can process various file types 
    including PDFs, text files, and JSON documents. You extract relevant information, 
    structure it properly, and prepare clean JSON output that can be easily consumed by 
    external systems. You handle different content types intelligently and always provide 
    structured, meaningful data extraction results.""",
    tools=[DataExtractionTool()],
    llm=llm,
    verbose=True,
    allow_delegation=False,
    max_iter=3
)

# Agent 4: Astra DB Storage Agent (for attachment metadata)
astra_db_agent = Agent(
    role="Astra DB Storage Specialist",
    goal="Store extracted attachment metadata in Astra DB invoice_attachments table",
    backstory="""You are a database storage expert specializing in Astra DB operations.
    Your role is to take extracted attachment metadata and store it properly in the Astra DB
    invoice_attachments table with all necessary metadata and timestamps.""",
    tools=[AstraDBTool()],
    llm=llm,
    verbose=True,
    max_iter=3
)

# Agent 5: Invoice Data Storage Agent (for structured invoice data)
invoice_data_agent = Agent(
    role="Invoice Data Storage Specialist", 
    goal="Store structured invoice data in Astra DB invoice_data table with audit trail",
    backstory="""You are a specialized database expert focused on storing structured invoice data.
    Your role is to take parsed invoice fields (amounts, dates, vendor info, etc.) and store them
    in the invoice_data table while maintaining proper audit trail references to the original
    attachment records.""",
    tools=[InvoiceDataStorageTool()],
    llm=llm,
    verbose=True,
    max_iter=3
)

# Agent 6: Monitoring Agent
monitoring_agent = Agent(
    role="System Monitoring Specialist",
    goal="Monitor the entire invoice processing workflow and provide status updates",
    backstory="""You are a system monitoring expert responsible for overseeing the complete
    invoice processing pipeline. You track the progress of each step, identify any failures
    or bottlenecks, and provide comprehensive status reports. You ensure data integrity
    and successful completion of the entire workflow from email search to final storage.""",
    tools=[],  # Monitoring agent uses built-in capabilities
    llm=llm,
    verbose=True,
    max_iter=2
)
