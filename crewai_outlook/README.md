# CrewAI Outlook Attachment Processing

A multi-agent AI system built with CrewAI that automates the process of searching Outlook emails, downloading attachments, extracting data, and sending it to external APIs.

## Architecture

The system consists of 4 specialized agents working in sequence:

1. **Email Search Agent** - Searches Outlook emails from specific senders and extracts attachment metadata
2. **Attachment Download Agent** - Downloads attachments using messageId and attachmentId
3. **Data Extraction Agent** - Extracts and structures data from downloaded attachments
4. **API Integration Agent** - Sends extracted data to external applications via API

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and endpoints
```

3. Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OUTLOOK_API_BASE_URL` - Your Outlook microservice URL (e.g., https://outlook-microservice.onrender.com)
- `OUTLOOK_API_KEY` - API key for your Outlook microservice
- `EXTERNAL_API_URL` - External API endpoint to send data to
- `EXTERNAL_API_KEY` - API key for external service (optional)

## Usage

### Command Line
```bash
python crew.py
```

### Programmatic Usage
```python
from crew import OutlookProcessingCrew

crew = OutlookProcessingCrew()
result = crew.run(
    sender_email="sender@example.com",
    subject_contains="invoice",
    days_back=7
)
```

## Workflow

1. **Search Phase**: Agent searches for emails from specified sender with attachments
2. **Download Phase**: Agent downloads all found attachments
3. **Extraction Phase**: Agent extracts data based on file type (PDF, text, JSON, etc.)
4. **Integration Phase**: Agent sends structured data to external API

## Supported File Types

- **PDF**: Text extraction using PyPDF2
- **Text files**: Direct content reading
- **JSON files**: Structured data parsing
- **Other files**: Basic metadata extraction

## Features

- Sequential agent workflow with context passing
- Robust error handling and logging
- Support for multiple attachment types
- Configurable search parameters
- Memory-enabled agents for better context retention
- Verbose logging for debugging

## API Integration

The system integrates with:
- Outlook microservice for email search and attachment download
- External APIs for data submission
- OpenAI for agent intelligence
