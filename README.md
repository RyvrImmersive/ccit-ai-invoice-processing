# CCIT.ai Agentic Invoice Data Processing

A production-ready agentic AI system for automated Outlook email invoice processing using CrewAI framework, with real-time monitoring, multi-database support, and scheduled automation.

## 🚀 Features

- **🤖 Agentic AI Processing**: 6 specialized CrewAI agents for complete workflow automation
- **📧 Outlook Integration**: Search and download email attachments via Render microservice
- **🔍 Multi-Invoice Extraction**: AI-powered extraction supporting multiple invoices per attachment
- **💾 Multi-Database Support**: Astra DB, PostgreSQL, MySQL, SQLite compatibility
- **📊 Real-time Monitoring**: Conversational web dashboard with live progress updates
- **⏰ Automated Scheduling**: Daily cron job execution with configurable parameters
- **🔒 Secure Configuration**: Environment-based configuration management
- **📋 Audit Trail**: Complete data lineage from raw attachments to structured records

## 🏗️ System Architecture

```
CCIT.ai Agentic Invoice Data Processing
├── crewai_outlook/          # Core CrewAI workflow
│   ├── agents.py           # 6 specialized AI agents
│   ├── tasks.py            # Workflow task definitions
│   ├── crew.py             # CrewAI orchestration
│   └── tools/              # Custom processing tools
├── frontend/               # Real-time monitoring dashboard
│   ├── app.py              # Flask-SocketIO server
│   ├── templates/          # Conversational UI
│   └── static/             # Logo and assets
├── scheduler/              # Automated daily processing
│   ├── daily_processor.py  # Cron job handler
│   └── scheduler_config.json # Schedule configuration
├── config/                 # Configuration management
│   └── config.py           # Multi-environment config
└── deployment/             # Production deployment files
```

## 🎯 AI Agents

1. **📧 Email Search Agent** - Discovers invoice emails with attachments
2. **📎 Attachment Download Agent** - Downloads PDF/document attachments  
3. **🔍 Data Extraction Agent** - AI-powered invoice data extraction (GPT-4)
4. **💾 Metadata Storage Agent** - Stores raw attachment metadata in database
5. **📋 Invoice Data Agent** - Stores structured invoice fields with audit trail
6. **📊 System Monitor Agent** - Provides conversational workflow updates

## 📊 Database Schema

### Invoice Attachments Table
```sql
- id (UUID, Primary Key)
- message_id (Outlook message ID)
- attachment_name (Original filename)
- sender_email (Email sender)
- subject (Email subject)
- content_type (MIME type)
- file_size (Size in bytes)
- extracted_data (JSON - Full extraction results)
- processing_status (completed/failed/pending)
- created_at (Timestamp)
```

### Invoice Data Table  
```sql
- id (UUID, Primary Key)
- attachment_record_id (Foreign Key - Audit trail)
- invoice_number (Invoice identifier)
- vendor_name (Supplier name)
- vendor_address (Supplier address)
- invoice_date (Invoice date)
- total_amount (Total amount)
- currency (Currency code)
- tax_amount (Tax amount)
- line_items (JSON array)
- bill_to_name (Customer name)
- confidence_score (AI extraction confidence)
- invoice_sequence (Multi-invoice support)
- created_at (Timestamp)
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and setup
git clone <repository-url>
cd outlook-mcp

# Install dependencies
pip install -r crewai_outlook/requirements.txt
pip install -r frontend/requirements.txt

# Copy environment template
cp crewai_outlook/.env.example crewai_outlook/.env
```

### 2. Configure Environment Variables

Edit `crewai_outlook/.env`:

```env
# Outlook Microservice (Required)
OUTLOOK_API_BASE_URL=https://your-outlook-microservice.onrender.com
OUTLOOK_API_KEY=your-api-key

# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key

# Database Configuration
DATABASE_TYPE=astra  # or postgresql, mysql, sqlite

# Astra DB Configuration (if using Astra)
ASTRA_DB_DATABASE_ID=your-database-id
ASTRA_DB_APPLICATION_TOKEN=your-token
ASTRA_DB_KEYSPACE=invoices
ASTRA_DB_REGION=us-east-1

# PostgreSQL Configuration (if using PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=invoice_processing
POSTGRES_USERNAME=user
POSTGRES_PASSWORD=password

# Processing Configuration
MAX_INVOICES_PER_ATTACHMENT=2
CONFIDENCE_THRESHOLD=0.7
RETRY_ATTEMPTS=3
```

### 3. Run the System

**Start Monitoring Dashboard:**
```bash
cd frontend
python app.py
# Access: http://localhost:5000
```

**Run Manual Processing:**
```bash
cd crewai_outlook
python crew.py
```

**Setup Daily Automation:**
```bash
cd scheduler
./setup_cron.sh
```

## 🔧 Configuration for Different Setups

### Different Email Account

1. **Update Outlook Microservice**: Deploy your microservice with new email credentials
2. **Update Environment**: Change `OUTLOOK_API_BASE_URL` and `OUTLOOK_API_KEY`
3. **Test Connection**: Run search to verify new email access

### Different Database

#### PostgreSQL Setup
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_DATABASE=invoice_processing
POSTGRES_USERNAME=your-username
POSTGRES_PASSWORD=your-password
```

#### MySQL Setup  
```env
DATABASE_TYPE=mysql
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_DATABASE=invoice_processing
MYSQL_USERNAME=your-username
MYSQL_PASSWORD=your-password
```

#### SQLite Setup
```env
DATABASE_TYPE=sqlite
SQLITE_DATABASE_PATH=/path/to/invoice_processing.db
```

### Different AI Provider

Update `crewai_outlook/tools/outlook_tools.py` to use different AI providers:

```python
# For Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# For Anthropic Claude
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

## 📊 Monitoring Dashboard

The conversational monitoring dashboard provides:

- **Real-time Progress**: Live updates during workflow execution
- **Conversational Interface**: Human-friendly status messages
- **Workflow Control**: Start/stop processing with custom parameters
- **Historical Data**: Processing statistics and logs
- **Error Tracking**: Detailed error reporting and troubleshooting

Access at: `http://localhost:5000`

## ⏰ Automated Scheduling

### Setup Daily Processing
```bash
cd scheduler
./setup_cron.sh
```

### Configure Schedule
Edit `scheduler/scheduler_config.json`:
```json
{
  "search_criteria": {
    "sender_email": "",
    "subject_contains": "invoice", 
    "days_back": 1
  },
  "schedule": {
    "enabled": true,
    "time": "09:00",
    "timezone": "UTC",
    "weekdays_only": true
  },
  "notification_webhook": "https://hooks.slack.com/your-webhook"
}
```

```bash
cd scheduler
python daily_processor.py
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose -f deployment/docker-compose.yml up -d

# Individual service builds
docker build -f deployment/Dockerfile.frontend -t invoice-frontend .
docker build -f deployment/Dockerfile.scheduler -t invoice-scheduler .
```

### Render Deployment
```bash
# Deploy using Render configuration
render-cli deploy --config deployment/render.yaml
```

## 🔍 Troubleshooting

### Common Issues

**Database Connection Errors:**
- Verify database credentials in `.env`
- Check network connectivity to database
- Ensure keyspace/database exists

**Outlook API Errors:**
- Validate `OUTLOOK_API_KEY` and `OUTLOOK_API_BASE_URL`
- Check microservice health endpoint
- Verify email account permissions

**AI Extraction Issues:**
- Confirm `OPENAI_API_KEY` is valid
- Check API rate limits and quotas
- Review confidence threshold settings

**Monitoring Dashboard Issues:**
- Ensure Flask-SocketIO dependencies installed
- Check port 5000 availability
- Verify static file serving

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
cd crewai_outlook
python crew.py
```

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Keys**: Rotate keys regularly and use least-privilege access
3. **Database Security**: Use SSL/TLS connections and strong passwords
4. **Network Security**: Deploy behind firewall/VPN for production
5. **Monitoring**: Enable logging and alerting for security events

## 📈 Performance Optimization

- **Database Indexing**: Create indexes on frequently queried fields
- **Batch Processing**: Process multiple attachments in parallel
- **Caching**: Cache frequently accessed configuration data
- **Resource Limits**: Set appropriate memory/CPU limits for containers

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📞 Support

For technical support or questions:
- Create GitHub issues for bugs/feature requests
- Review troubleshooting section for common problems
- Check logs for detailed error information

## License

MIT License
