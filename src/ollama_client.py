import ollama
from typing import Dict, Optional
from config.settings import settings

class OllamaClient:
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_host)
        self.model = settings.ollama_model
    
    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\n{prompt}"
            
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                stream=False
            )
            
            return response['response']
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I'm unable to generate a response at this time."
    
    def classify_email(self, email_data: Dict) -> Dict:
        classification_prompt = f"""
        Analyze this email and classify it:

        Subject: {email_data['subject']}
        From: {email_data['sender']}
        Body: {email_data['body'][:500]}...

        Classify this email and respond with ONLY a JSON object:
        {{
            "category": "spam|personal|work|urgent|promotional|newsletter",
            "priority": "high|medium|low",
            "requires_response": true|false,
            "sentiment": "positive|neutral|negative",
            "action_needed": "reply|acknowledge|schedule|ignore"
        }}
        """
        
        try:
            response = self.generate_response(classification_prompt)
            import json
            return json.loads(response.strip())
        except Exception as e:
            print(f"Error classifying email: {e}")
            return {
                "category": "unknown",
                "priority": "medium",
                "requires_response": False,
                "sentiment": "neutral",
                "action_needed": "ignore"
            }
    
    def generate_email_response(self, email_data: Dict, classification: Dict) -> str:
        response_prompt = f"""
        You are Michael Sigamani's personal AI assistant. Generate a professional email response.

        Original Email:
        Subject: {email_data['subject']}
        From: {email_data['sender']}
        Body: {email_data['body']}

        Email Classification:
        Category: {classification['category']}
        Priority: {classification['priority']}
        Action: {classification['action_needed']}

        Guidelines:
        - Be professional and concise
        - Match the tone of the original email
        - If it's a meeting request, suggest alternative times
        - If it's a question, provide helpful information
        - If it's promotional/spam, politely decline
        - Keep responses under 150 words
        - Sign as "Michael" or "Best regards, Michael"

        Generate a response:
        """
        
        return self.generate_response(response_prompt)
    
    def should_auto_respond(self, classification: Dict) -> bool:
        auto_respond_categories = ['promotional', 'newsletter', 'spam']
        safe_actions = ['acknowledge', 'reply']
        
        return (
            classification['category'] in auto_respond_categories or
            (classification['priority'] == 'low' and 
             classification['action_needed'] in safe_actions)
        )
