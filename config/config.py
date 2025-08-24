#!/usr/bin/env python3
"""
Configuration management for CrewAI Invoice Processing System
Centralizes all configuration with support for different environments and databases
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class OutlookConfig:
    """Outlook API configuration"""
    api_base_url: str
    api_key: str
    
    @classmethod
    def from_env(cls):
        return cls(
            api_base_url=os.getenv('OUTLOOK_API_BASE_URL', ''),
            api_key=os.getenv('OUTLOOK_API_KEY', '')
        )

@dataclass
class DatabaseConfig:
    """Database configuration - supports multiple database types"""
    db_type: str  # 'astra', 'postgresql', 'mysql', 'sqlite'
    connection_params: Dict[str, Any]
    
    @classmethod
    def from_env(cls):
        db_type = os.getenv('DATABASE_TYPE', 'astra').lower()
        
        if db_type == 'astra':
            return cls(
                db_type='astra',
                connection_params={
                    'database_id': os.getenv('ASTRA_DB_DATABASE_ID'),
                    'application_token': os.getenv('ASTRA_DB_APPLICATION_TOKEN'),
                    'keyspace': os.getenv('ASTRA_DB_KEYSPACE'),
                    'secure_connect_bundle': os.getenv('ASTRA_DB_SECURE_CONNECT_BUNDLE'),
                    'region': os.getenv('ASTRA_DB_REGION', 'us-east-1')
                }
            )
        elif db_type == 'postgresql':
            return cls(
                db_type='postgresql',
                connection_params={
                    'host': os.getenv('POSTGRES_HOST', 'localhost'),
                    'port': int(os.getenv('POSTGRES_PORT', '5432')),
                    'database': os.getenv('POSTGRES_DATABASE'),
                    'username': os.getenv('POSTGRES_USERNAME'),
                    'password': os.getenv('POSTGRES_PASSWORD'),
                    'ssl_mode': os.getenv('POSTGRES_SSL_MODE', 'prefer')
                }
            )
        elif db_type == 'mysql':
            return cls(
                db_type='mysql',
                connection_params={
                    'host': os.getenv('MYSQL_HOST', 'localhost'),
                    'port': int(os.getenv('MYSQL_PORT', '3306')),
                    'database': os.getenv('MYSQL_DATABASE'),
                    'username': os.getenv('MYSQL_USERNAME'),
                    'password': os.getenv('MYSQL_PASSWORD'),
                    'ssl_disabled': os.getenv('MYSQL_SSL_DISABLED', 'false').lower() == 'true'
                }
            )
        elif db_type == 'sqlite':
            return cls(
                db_type='sqlite',
                connection_params={
                    'database_path': os.getenv('SQLITE_DATABASE_PATH', 'invoice_processing.db')
                }
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

@dataclass
class AIConfig:
    """AI/OpenAI configuration"""
    openai_api_key: str
    model: str
    temperature: float
    max_tokens: int
    
    @classmethod
    def from_env(cls):
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        )

@dataclass
class ProcessingConfig:
    """Invoice processing configuration"""
    max_invoices_per_attachment: int
    confidence_threshold: float
    retry_attempts: int
    timeout_seconds: int
    
    @classmethod
    def from_env(cls):
        return cls(
            max_invoices_per_attachment=int(os.getenv('MAX_INVOICES_PER_ATTACHMENT', '2')),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.7')),
            retry_attempts=int(os.getenv('RETRY_ATTEMPTS', '3')),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', '300'))
        )

class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """Initialize configuration manager"""
        self.config_file = config_file or 'config.json'
        self.env_file = env_file or '.env'
        
        # Load environment variables
        if Path(self.env_file).exists():
            load_dotenv(self.env_file)
        
        # Load configurations
        self.outlook = OutlookConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.ai = AIConfig.from_env()
        self.processing = ProcessingConfig.from_env()
        
        # Load additional config from JSON file
        self.additional_config = self._load_json_config()
    
    def _load_json_config(self) -> Dict[str, Any]:
        """Load additional configuration from JSON file"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {self.config_file}: {e}")
        
        return {}
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return any issues"""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        # Validate Outlook config
        if not self.outlook.api_base_url:
            issues['errors'].append("OUTLOOK_API_BASE_URL is required")
        if not self.outlook.api_key:
            issues['errors'].append("OUTLOOK_API_KEY is required")
        
        # Validate AI config
        if not self.ai.openai_api_key:
            issues['errors'].append("OPENAI_API_KEY is required")
        
        # Validate database config
        if self.database.db_type == 'astra':
            if not self.database.connection_params.get('database_id'):
                issues['errors'].append("ASTRA_DB_DATABASE_ID is required for Astra DB")
            if not self.database.connection_params.get('application_token'):
                issues['errors'].append("ASTRA_DB_APPLICATION_TOKEN is required for Astra DB")
        
        # Validate processing config
        if self.processing.confidence_threshold < 0 or self.processing.confidence_threshold > 1:
            issues['warnings'].append("CONFIDENCE_THRESHOLD should be between 0 and 1")
        
        return issues
    
    def get_database_connection_string(self) -> str:
        """Generate database connection string based on type"""
        db_type = self.database.db_type
        params = self.database.connection_params
        
        if db_type == 'postgresql':
            return f"postgresql://{params['username']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        elif db_type == 'mysql':
            return f"mysql://{params['username']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        elif db_type == 'sqlite':
            return f"sqlite:///{params['database_path']}"
        else:
            return ""  # Astra DB uses different connection method
    
    def export_config_template(self, output_file: str = 'config_template.json'):
        """Export a configuration template"""
        template = {
            "outlook": {
                "api_base_url": "https://your-outlook-microservice.onrender.com",
                "api_key": "your-api-key-here"
            },
            "database": {
                "type": "astra",  # or postgresql, mysql, sqlite
                "astra": {
                    "database_id": "your-database-id",
                    "application_token": "your-token",
                    "keyspace": "invoices",
                    "region": "us-east-1"
                },
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "invoice_processing",
                    "username": "user",
                    "password": "password"
                }
            },
            "ai": {
                "openai_api_key": "your-openai-key",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "processing": {
                "max_invoices_per_attachment": 2,
                "confidence_threshold": 0.7,
                "retry_attempts": 3,
                "timeout_seconds": 300
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Configuration template exported to {output_file}")

# Global configuration instance
config = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration instance"""
    return config

def validate_environment():
    """Validate the current environment configuration"""
    issues = config.validate_config()
    
    if issues['errors']:
        print("❌ Configuration Errors:")
        for error in issues['errors']:
            print(f"   • {error}")
        return False
    
    if issues['warnings']:
        print("⚠️ Configuration Warnings:")
        for warning in issues['warnings']:
            print(f"   • {warning}")
    
    if not issues['errors'] and not issues['warnings']:
        print("✅ Configuration is valid")
    
    return True

if __name__ == "__main__":
    # Validate configuration when run directly
    validate_environment()
    
    # Export template if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--export-template":
        config.export_config_template()
