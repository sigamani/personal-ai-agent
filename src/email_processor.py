import logging
from typing import List, Dict
from datetime import datetime
from src.gmail_client import GmailClient
from src.ollama_client import OllamaClient
from config.settings import settings

logging.basicConfig(level=settings.log_level, filename=settings.log_file)
logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.gmail_client = GmailClient()
        self.ollama_client = OllamaClient()
        
        if not self.ollama_client.is_available():
            logger.warning("Ollama is not available. Email processing will be limited.")
    
    def process_emails(self) -> Dict:
        logger.info("Starting email processing cycle")
        
        unread_emails = self.gmail_client.get_unread_emails(
            max_results=settings.max_emails_per_check
        )
        
        if not unread_emails:
            logger.info("No unread emails found")
            return {"processed": 0, "responded": 0, "drafts_created": 0}
        
        processed_count = 0
        responded_count = 0
        drafts_created = 0
        
        for email in unread_emails:
            try:
                result = self._process_single_email(email)
                processed_count += 1
                
                if result['action'] == 'responded':
                    responded_count += 1
                elif result['action'] == 'draft_created':
                    drafts_created += 1
                
                logger.info(f"Processed email: {email['subject'][:50]}... - Action: {result['action']}")
                
            except Exception as e:
                logger.error(f"Error processing email {email['id']}: {e}")
        
        summary = {
            "processed": processed_count,
            "responded": responded_count,
            "drafts_created": drafts_created,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Email processing complete: {summary}")
        return summary
    
    def _process_single_email(self, email: Dict) -> Dict:
        if not self.ollama_client.is_available():
            self.gmail_client.mark_as_read(email['id'])
            return {"action": "marked_read", "reason": "ollama_unavailable"}
        
        classification = self.ollama_client.classify_email(email)
        
        logger.info(f"Email classified: {classification}")
        
        if classification['action_needed'] == 'ignore':
            self.gmail_client.mark_as_read(email['id'])
            return {"action": "ignored", "classification": classification}
        
        if not classification['requires_response']:
            self.gmail_client.mark_as_read(email['id'])
            return {"action": "marked_read", "classification": classification}
        
        response_content = self.ollama_client.generate_email_response(email, classification)
        
        should_auto_send = (
            settings.auto_send_responses and 
            self.ollama_client.should_auto_respond(classification)
        )
        
        if should_auto_send:
            success = self.gmail_client.send_reply(email, response_content)
            if success:
                self.gmail_client.mark_as_read(email['id'])
                return {
                    "action": "responded", 
                    "classification": classification,
                    "auto_sent": True
                }
        
        success = self.gmail_client.create_draft_reply(email, response_content)
        if success:
            self.gmail_client.mark_as_read(email['id'])
            return {
                "action": "draft_created",
                "classification": classification,
                "response_preview": response_content[:100] + "..."
            }
        
        return {"action": "failed", "classification": classification}
    
    def get_processing_stats(self) -> Dict:
        return {
            "gmail_authenticated": self.gmail_client.service is not None,
            "ollama_available": self.ollama_client.is_available(),
            "auto_send_enabled": settings.auto_send_responses,
            "check_interval": settings.check_interval_minutes,
            "model": settings.ollama_model
        }