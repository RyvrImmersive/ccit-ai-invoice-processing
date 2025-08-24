# CCIT.ai System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CCIT.ai Agentic Invoice Processing                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email Source  │    │  AI Processing  │    │   Data Storage  │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Outlook   │ │───▶│ │   CrewAI    │ │───▶│ │  Astra DB   │ │
│ │   Emails    │ │    │ │  6 Agents   │ │    │ │ PostgreSQL  │ │
│ │ Attachments │ │    │ │   GPT-4     │ │    │ │   MySQL     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │   SQLite    │ │
└─────────────────┘    └─────────────────┘    │ └─────────────┘ │
                                              └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Monitoring & Control                               │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Flask     │    │  Real-time  │    │  Automated  │    │ Production  │     │
│  │ Dashboard   │    │ SocketIO    │    │ Scheduler   │    │ Deployment  │     │
│  │   (Web)     │    │  Updates    │    │ (Cron Jobs) │    │ (Render)    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🤖 CrewAI Agent Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            6 Specialized AI Agents                              │
└─────────────────────────────────────────────────────────────────────────────────┘

    📧 Email Search Agent
    ┌─────────────────────┐
    │ • Search Outlook    │
    │ • Find attachments  │
    │ • Extract metadata  │
    └──────────┬──────────┘
               │
               ▼
    📎 Attachment Download Agent
    ┌─────────────────────┐
    │ • Download PDFs     │
    │ • Validate files    │
    │ • Handle errors     │
    └──────────┬──────────┘
               │
               ▼
    🔍 Data Extraction Agent
    ┌─────────────────────┐
    │ • AI-powered OCR    │
    │ • Multi-invoice     │
    │ • Structure data    │
    └──────────┬──────────┘
               │
               ▼
    💾 Metadata Storage Agent
    ┌─────────────────────┐
    │ • Store raw data    │
    │ • Create audit ID   │
    │ • Log processing    │
    └──────────┬──────────┘
               │
               ▼
    📋 Invoice Data Agent
    ┌─────────────────────┐
    │ • Store invoices    │
    │ • Link audit trail  │
    │ • Validate schema   │
    └──────────┬──────────┘
               │
               ▼
    📊 System Monitor Agent
    ┌─────────────────────┐
    │ • Real-time updates │
    │ • Status reporting  │
    │ • Error handling    │
    └─────────────────────┘
```

## 🗄️ Database Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Multi-Database Support                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Astra DB      │    │   PostgreSQL    │    │   MySQL/SQLite  │
│   (Primary)     │    │   (Alternative) │    │   (Alternative) │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Keyspace:   │ │    │ │ Database:   │ │    │ │ Database:   │ │
│ │ invoices    │ │    │ │ invoice_db  │ │    │ │ invoice_db  │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ │ Tables:     │ │    │ │ Tables:     │ │    │ │ Tables:     │ │
│ │ • invoice_  │ │    │ │ • invoice_  │ │    │ │ • invoice_  │ │
│ │   attachments│ │    │ │   attachments│ │    │ │   attachments│ │
│ │ • invoice_  │ │    │ │ • invoice_  │ │    │ │ • invoice_  │ │
│ │   data      │ │    │ │   data      │ │    │ │   data      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Database Schema                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

invoice_attachments                    invoice_data
┌─────────────────────┐               ┌─────────────────────┐
│ id (UUID, PK)       │               │ id (UUID, PK)       │
│ message_id          │               │ attachment_record_id│ ◄─┐
│ attachment_name     │               │ invoice_number      │   │
│ sender_email        │               │ vendor_name         │   │
│ subject             │               │ vendor_address      │   │
│ content_type        │               │ invoice_date        │   │
│ file_size           │               │ total_amount        │   │
│ extracted_data      │ ──────────────│ currency            │   │
│ processing_status   │    (JSON)     │ tax_amount          │   │
│ created_at          │               │ line_items          │   │
└─────────────────────┘               │ bill_to_name        │   │
                                      │ confidence_score    │   │
                                      │ invoice_sequence    │   │
                                      │ created_at          │   │
                                      └─────────────────────┘   │
                                                                │
                                      Audit Trail Relationship ─┘
```

## 🌐 Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              External Services                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

Internet
    │
    ├─── Outlook Microservice (Render)
    │    https://outlook-microservice.onrender.com
    │    ┌─────────────────────┐
    │    │ • /search endpoint  │
    │    │ • /download endpoint│
    │    │ • Authentication    │
    │    └─────────────────────┘
    │
    ├─── OpenAI API
    │    ┌─────────────────────┐
    │    │ • GPT-4 Processing  │
    │    │ • Invoice Extraction│
    │    │ • AI Intelligence   │
    │    └─────────────────────┘
    │
    └─── Astra DB (DataStax)
         ┌─────────────────────┐
         │ • Cloud Database    │
         │ • Global Scale      │
         │ • High Availability │
         └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Local Components                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

Local Machine / Cloud Instance
    │
    ├─── CrewAI Workflow Engine
    │    ┌─────────────────────┐
    │    │ • Agent Orchestration│
    │    │ • Task Management   │
    │    │ • Error Handling    │
    │    └─────────────────────┘
    │
    ├─── Flask Dashboard (Port 5000)
    │    ┌─────────────────────┐
    │    │ • Real-time UI      │
    │    │ • SocketIO Updates  │
    │    │ • Status Monitoring │
    │    └─────────────────────┘
    │
    └─── Scheduler Service
         ┌─────────────────────┐
         │ • Cron Jobs         │
         │ • Automated Runs    │
         │ • Background Tasks  │
         └─────────────────────┘
```

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Production Deployment                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Netlify     │    │     Render      │    │     Docker      │
│   (Static UI)   │    │   (Dynamic)     │    │    (Local)      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Dashboard   │ │    │ │ Web Service │ │    │ │ Frontend    │ │
│ │ (HTML/JS)   │ │    │ │ Background  │ │    │ │ Scheduler   │ │
│ │ Real Data   │ │    │ │ Scheduler   │ │    │ │ Database    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Environment Variables Flow:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ .env.example → .env → Environment Variables → Services                         │
│                                                                                 │
│ • OPENAI_API_KEY                                                               │
│ • OUTLOOK_API_KEY                                                              │
│ • ASTRA_DB_*                                                                   │
│ • FLASK_SECRET_KEY                                                             │
│ • DATABASE_TYPE                                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              End-to-End Data Flow                               │
└─────────────────────────────────────────────────────────────────────────────────┘

1. Email Discovery
   Outlook → Search API → Email Metadata
   
2. Attachment Processing  
   Email → Download API → PDF Files
   
3. AI Extraction
   PDF → OpenAI GPT-4 → Structured JSON
   
4. Data Storage
   JSON → Database → Audit Trail
   
5. Real-time Updates
   Database → Dashboard → Live UI
   
6. Automated Processing
   Scheduler → Workflow → Continuous Operation

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Security Architecture                              │
└─────────────────────────────────────────────────────────────────────────────────┘

• API Key Management (Environment Variables)
• Database SSL/TLS Connections  
• Secure Token Authentication
• Input Validation & Sanitization
• Error Handling & Logging
• Rate Limiting & Retry Logic
```

## 📊 Performance & Scalability

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Scalability Features                              │
└─────────────────────────────────────────────────────────────────────────────────┘

• Multi-Database Support (Horizontal Scaling)
• Async Processing (Non-blocking Operations)  
• Cloud-Native Deployment (Auto-scaling)
• Modular Agent Architecture (Independent Scaling)
• Configurable Batch Processing
• Resource Monitoring & Optimization
```

This architecture supports processing thousands of invoices daily with high availability, fault tolerance, and real-time monitoring capabilities.
