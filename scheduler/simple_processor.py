#!/usr/bin/env python3
"""
Simplified daily processor that directly calls the CrewAI system
without complex path dependencies
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def run_crewai_processing():
    """Run the CrewAI processing using direct subprocess call"""
    try:
        logger.info("🚀 Starting daily invoice processing")
        logger.info(f"📅 Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Change to the crewai_outlook directory
        crewai_dir = Path(__file__).parent.parent / 'crewai_outlook'
        
        # Set environment variables for the subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = str(crewai_dir)
        
        # Run the main crew script
        cmd = [
            sys.executable, 
            '-c',
            '''
import sys
sys.path.insert(0, ".")
from crew import OutlookProcessingCrew
crew = OutlookProcessingCrew()
result = crew.run(sender_email="", subject_contains="invoice", days_back=1)
print("SUCCESS:", result)
'''
        ]
        
        logger.info(f"🤖 Executing: {' '.join(cmd)}")
        logger.info(f"📁 Working directory: {crewai_dir}")
        
        result = subprocess.run(
            cmd,
            cwd=crewai_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Processing completed successfully")
            logger.info(f"📊 Output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Processing failed with return code: {result.returncode}")
            logger.error(f"📊 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Processing timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return False

def main():
    """Main entry point"""
    try:
        success = run_crewai_processing()
        exit_code = 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
        exit_code = 130
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        exit_code = 1
    
    logger.info("=" * 60)
    logger.info(f"🏁 Daily processing finished with exit code: {exit_code}")
    logger.info("=" * 60)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
