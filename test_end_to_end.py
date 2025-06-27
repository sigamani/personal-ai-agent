#!/usr/bin/env python3
"""
End-to-end test: Process incoming email and create automated response
"""

import time
import json
from datetime import datetime
from src.email_processor import EmailProcessor

def run_end_to_end_test():
    print("🤖 Personal AI Assistant - End-to-End Test")
    print("=" * 60)
    
    print("STEP 1: Please send a test email")
    print("From: sigamani1982@gmail.com")
    print("To: michael.sigamani@gmail.com")
    print("Subject: Test Email for AI Assistant")
    print("Body: Can you help me schedule a meeting for next week?")
    print()
    
    input("Press Enter after you've sent the email...")
    print("\nWaiting 30 seconds for email to arrive...")
    time.sleep(30)
    
    print("\nSTEP 2: Processing emails with AI assistant...")
    processor = EmailProcessor()
    
    # Show system status
    stats = processor.get_processing_stats()
    print(f"System Status:")
    print(f"  Gmail: {'✓' if stats['gmail_authenticated'] else '✗'}")
    print(f"  Ollama: {'✓' if stats['ollama_available'] else '✗'}")
    print(f"  Model: {stats['model']}")
    print(f"  Auto-send: {'✓' if stats['auto_send_enabled'] else '✗ (Draft mode)'}")
    print()
    
    # Process emails
    print("Processing unread emails...")
    result = processor.process_emails()
    
    print(f"\nSTEP 3: Processing Results:")
    print(f"  Emails processed: {result['processed']}")
    print(f"  Responses sent: {result['responded']}")
    print(f"  Drafts created: {result['drafts_created']}")
    print(f"  Timestamp: {result['timestamp']}")
    
    if result['processed'] > 0:
        print("\n✅ SUCCESS! Check your Gmail drafts folder for the AI-generated response.")
        print("\nThe AI assistant:")
        print("  1. Detected the new email from sigamani1982@gmail.com")
        print("  2. Classified it (work/personal/urgent/etc.)")
        print("  3. Generated an appropriate response using Llama 14B")
        print("  4. Created a draft reply (safe mode)")
        print("  5. Marked the original email as read")
        
        # Show logs
        print("\nCheck logs for detailed processing info:")
        print("  tail -f logs/agent.log")
        
    else:
        print("\n⚠️  No emails were processed. Possible reasons:")
        print("  - Email hasn't arrived yet (try waiting longer)")
        print("  - Email was already marked as read")
        print("  - Authentication issues")
        
        print("\nTrying to get recent emails...")
        try:
            unread_emails = processor.gmail_client.get_unread_emails(max_results=5)
            print(f"Found {len(unread_emails)} unread emails:")
            for email in unread_emails:
                print(f"  - From: {email['sender']}")
                print(f"    Subject: {email['subject']}")
                print(f"    Snippet: {email['snippet'][:100]}...")
                print()
        except Exception as e:
            print(f"Error checking emails: {e}")
    
    return result['processed'] > 0

def monitor_mode():
    """Continuous monitoring mode"""
    print("\n🔄 Continuous Monitoring Mode")
    print("Press Ctrl+C to stop...")
    
    processor = EmailProcessor()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking for new emails...")
            result = processor.process_emails()
            
            if result['processed'] > 0:
                print(f"✅ Processed {result['processed']} emails, created {result['drafts_created']} drafts")
            else:
                print("📭 No new emails to process")
            
            print("Waiting 60 seconds...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_mode()
    else:
        success = run_end_to_end_test()
        
        if success:
            print("\nWould you like to start continuous monitoring? (y/n)")
            if input().lower().startswith('y'):
                monitor_mode()