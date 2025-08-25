#!/usr/bin/env python3
"""
Main entry point for CrewAI invoice processing
Supports command line arguments for automated execution
"""

import argparse
import sys
from crew import OutlookProcessingCrew

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='CrewAI Outlook Invoice Processing')
    parser.add_argument('--sender-email', default='', help='Sender email to search for')
    parser.add_argument('--subject-contains', default='invoice', help='Subject filter')
    parser.add_argument('--days-back', type=int, default=1, help='Days back to search')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting CrewAI Outlook processing...")
    print(f"📧 Sender: {args.sender_email or 'Any'}")
    print(f"📋 Subject filter: {args.subject_contains}")
    print(f"📅 Days back: {args.days_back}")
    print("-" * 50)
    
    try:
        # Initialize and run the crew
        crew = OutlookProcessingCrew()
        result = crew.run(
            sender_email=args.sender_email,
            subject_contains=args.subject_contains,
            days_back=args.days_back
        )
        
        print("\n" + "="*50)
        print("🎉 WORKFLOW COMPLETED!")
        print("="*50)
        print(result)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
