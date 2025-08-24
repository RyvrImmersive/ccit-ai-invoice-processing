# CCIT.ai Invoice Processing - Complete Deployment Guide

## 🚀 Step-by-Step Infrastructure Setup

This guide will help you deploy the CCIT.ai Agentic Invoice Processing system on your own infrastructure.

## 📋 Prerequisites

- Python 3.8+
- Git
- Access to Outlook email account
- One of the following databases:
  - Astra DB (recommended)
  - PostgreSQL
  - MySQL
  - SQLite

## 🔧 Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/RyvrImmersive/ccit-ai-invoice-processing.git
cd ccit-ai-invoice-processing

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r crewai_outlook/requirements.txt
pip install -r frontend/requirements.txt
```

## 🔑 Step 2: Configure Environment Variables

```bash
# Copy environment template
cp crewai_outlook/.env.example crewai_outlook/.env

# Edit the .env file with your credentials
nano crewai_outlook/.env
```

### Required Environment Variables:

```env
# OpenAI API Key (Required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Outlook Microservice Configuration (Required)
OUTLOOK_API_BASE_URL=https://your-outlook-microservice.onrender.com
OUTLOOK_API_KEY=your-outlook-api-key

# Database Configuration (Choose one)
DATABASE_TYPE=astra  # or postgresql, mysql, sqlite

# Flask Configuration
FLASK_SECRET_KEY=your-64-character-random-string

# Processing Configuration
MAX_INVOICES_PER_ATTACHMENT=2
CONFIDENCE_THRESHOLD=0.7
RETRY_ATTEMPTS=3
```

### Database-Specific Configuration:

**For Astra DB (Recommended):**
```env
ASTRA_DB_DATABASE_ID=your-database-id
ASTRA_DB_APPLICATION_TOKEN=your-token
ASTRA_DB_KEYSPACE=invoices
ASTRA_DB_REGION=us-east-1
```

**For PostgreSQL:**
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=invoice_processing
POSTGRES_USERNAME=your-username
POSTGRES_PASSWORD=your-password
```

**For MySQL:**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=invoice_processing
MYSQL_USERNAME=your-username
MYSQL_PASSWORD=your-password
```

**For SQLite:**
```env
SQLITE_DATABASE_PATH=/path/to/invoice_processing.db
```

## 📧 Step 3: Setup Outlook Integration

### Option A: Use Existing Microservice
```env
# Use the public microservice (limited access)
OUTLOOK_API_BASE_URL=https://outlook-microservice.onrender.com
OUTLOOK_API_KEY=contact-admin-for-key
```

### Option B: Deploy Your Own Microservice
1. Clone the Outlook microservice repository
2. Configure with your Outlook credentials
3. Deploy to Render/Heroku/AWS
4. Update `OUTLOOK_API_BASE_URL` and `OUTLOOK_API_KEY`

## 🗄️ Step 4: Database Setup

### Astra DB Setup (Recommended)
1. Go to https://astra.datastax.com
2. Create free account and database
3. Create keyspace: `invoices`
4. Get Database ID and Application Token
5. Update `.env` with credentials

### PostgreSQL Setup
```sql
-- Create database
CREATE DATABASE invoice_processing;

-- Create tables (auto-created by application)
-- Tables: invoice_attachments, invoice_data
```

### MySQL Setup
```sql
-- Create database
CREATE DATABASE invoice_processing;

-- Grant permissions
GRANT ALL PRIVILEGES ON invoice_processing.* TO 'your-user'@'%';
```

### SQLite Setup
```bash
# SQLite database will be created automatically
# Just ensure the directory exists and is writable
mkdir -p /path/to/database/
```

## 🔐 Step 5: Generate Security Keys

```bash
# Generate Flask secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env file
echo "FLASK_SECRET_KEY=generated-key-here" >> crewai_outlook/.env
```

## 🧪 Step 6: Test Local Setup

```bash
# Test database connection
cd crewai_outlook
python -c "from config.config import get_database_config; print('✅ Database config loaded')"

# Test CrewAI agents
python -c "from crew import OutlookProcessingCrew; print('✅ CrewAI ready')"

# Start dashboard
cd ../frontend
python app.py
# Access: http://localhost:5000

# Test invoice processing
cd ../crewai_outlook
python crew.py
# Enter your email when prompted
```

## 🚀 Step 7: Production Deployment Options

### Option A: Render Deployment (Recommended)

1. **Fork the repository** to your GitHub account

2. **Go to Render.com** and create account

3. **Create Blueprint deployment:**
   - New → Blueprint
   - Connect your forked repository
   - Select `deployment/render.yaml`

4. **Configure environment variables** in Render dashboard:
   ```
   OPENAI_API_KEY=your-key
   OUTLOOK_API_KEY=your-key
   ASTRA_DB_DATABASE_ID=your-id
   ASTRA_DB_APPLICATION_TOKEN=your-token
   ASTRA_DB_KEYSPACE=invoices
   FLASK_SECRET_KEY=your-secret
   ```

5. **Deploy services:**
   - Dashboard service (Web)
   - Scheduler service (Background)

### Option B: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option C: Manual Server Deployment

```bash
# On your server
git clone https://github.com/your-username/ccit-ai-invoice-processing.git
cd ccit-ai-invoice-processing

# Install dependencies
pip install -r crewai_outlook/requirements.txt
pip install -r frontend/requirements.txt

# Configure environment
cp crewai_outlook/.env.example crewai_outlook/.env
# Edit .env with your credentials

# Start services with process manager (PM2, systemd, etc.)
pm2 start frontend/app.py --name ccit-dashboard
pm2 start scheduler/daily_processor.py --name ccit-scheduler
```

## ⏰ Step 8: Setup Automated Processing

### Local Cron Setup
```bash
# Setup daily processing
cd scheduler
./setup_cron.sh

# Verify cron job
crontab -l
```

### Cloud Scheduler Setup
For Render/cloud deployments, the background service handles scheduling automatically.

## 📊 Step 9: Configure Monitoring

### Dashboard Access
- Local: `http://localhost:5000`
- Production: `https://your-app.onrender.com`

### Log Monitoring
```bash
# Local logs
tail -f frontend/app.log
tail -f scheduler/daily_processor.log

# Render logs
render logs your-service-name --tail
```

## 🔍 Step 10: Verify Deployment

### Health Checks
```bash
# Test dashboard
curl http://localhost:5000/health

# Test API
curl http://localhost:5000/api/dashboard

# Test database connection
curl http://localhost:5000/api/test-db
```

### End-to-End Test
1. Send test invoice email to your account
2. Run manual processing: `python crew.py`
3. Check dashboard for new invoice
4. Verify database storage

## 🛠️ Customization Options

### Different Email Provider
1. Modify `crewai_outlook/tools/outlook_tools.py`
2. Update API endpoints and authentication
3. Test email search and download functions

### Different AI Provider
```python
# In crewai_outlook/tools/outlook_tools.py
# Replace OpenAI with your preferred provider

# Azure OpenAI
from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Anthropic Claude
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Custom Database Schema
1. Modify `config/config.py`
2. Update table definitions
3. Adjust agent storage logic

## 🔒 Security Best Practices

1. **Environment Variables:**
   - Never commit `.env` files
   - Use secure key management in production
   - Rotate API keys regularly

2. **Database Security:**
   - Use SSL/TLS connections
   - Implement proper access controls
   - Regular security updates

3. **Network Security:**
   - Deploy behind firewall/VPN
   - Use HTTPS for all endpoints
   - Implement rate limiting

## 📞 Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Test database connectivity
python -c "from services.astra_service import test_connection; test_connection()"
```

**Outlook API Errors:**
```bash
# Test API connectivity
curl -H "X-API-Key: your-key" https://your-outlook-api.com/health
```

**Missing Dependencies:**
```bash
# Reinstall requirements
pip install --upgrade -r crewai_outlook/requirements.txt
```

**Permission Errors:**
```bash
# Fix file permissions
chmod +x scheduler/setup_cron.sh
chmod +x scheduler/daily_processor.py
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python crew.py
```

## 📈 Scaling Considerations

### High Volume Processing
- Use PostgreSQL/MySQL for better performance
- Implement connection pooling
- Add Redis for caching
- Use load balancers for multiple instances

### Multi-Tenant Setup
- Separate databases per tenant
- Environment variable per deployment
- Isolated processing queues

## 🤝 Support

For technical support:
- GitHub Issues: https://github.com/RyvrImmersive/ccit-ai-invoice-processing/issues
- Documentation: README.md and ARCHITECTURE.md
- Example configurations in deployment/ folder

## 📄 License

MIT License - see LICENSE file for details.

---

**🎉 Congratulations!** You now have a fully functional CCIT.ai Agentic Invoice Processing system running on your infrastructure.
