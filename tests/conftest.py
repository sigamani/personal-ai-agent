import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service"""
    service = Mock()
    
    # Mock messages list
    service.users().messages().list.return_value.execute.return_value = {
        'messages': [
            {'id': 'test_email_1', 'threadId': 'thread_1'},
            {'id': 'test_email_2', 'threadId': 'thread_2'}
        ]
    }
    
    # Mock message get
    service.users().messages().get.return_value.execute.return_value = {
        'id': 'test_email_1',
        'threadId': 'thread_1',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Email for AI Assistant'},
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Date', 'value': 'Fri, 27 Jun 2025 09:10:25 +0100'}
            ],
            'mimeType': 'text/plain',
            'body': {
                'data': 'Q2FuIHlvdSBoZWxwIG1lIHNjaGVkdWxlIGEgbWVldGluZyBmb3IgbmV4dCB3ZWVrPw=='  # base64 encoded test message
            }
        },
        'snippet': 'Can you help me schedule a meeting for next week?'
    }
    
    # Mock draft creation
    service.users().drafts().create.return_value.execute.return_value = {
        'id': 'draft_123',
        'message': {'id': 'message_456'}
    }
    
    # Mock message modify (mark as read)
    service.users().messages().modify.return_value.execute.return_value = {}
    
    return service

@pytest.fixture
def mock_gmail_client(mock_gmail_service):
    """Mock Gmail client with service"""
    from src.gmail_client import GmailClient
    
    client = GmailClient.__new__(GmailClient)
    client.service = mock_gmail_service
    return client

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client"""
    from src.ollama_client import OllamaClient
    
    client = OllamaClient.__new__(OllamaClient)
    client.client = Mock()
    client.model = "llama3:8b"
    
    # Mock is_available
    client.is_available = Mock(return_value=True)
    
    # Mock generate_response
    def mock_generate_response(prompt, context=None):
        if "classify" in prompt.lower() or "json" in prompt.lower():
            return '{"category": "work", "priority": "medium", "requires_response": true, "sentiment": "neutral", "action_needed": "reply"}'
        else:
            return "Thank you for your email. I'll be happy to help you schedule a meeting for next week. Could you please let me know your availability? Best regards, Michael"
    
    client.generate_response = Mock(side_effect=mock_generate_response)
    
    # Mock classify_email
    client.classify_email = Mock(return_value={
        "category": "work",
        "priority": "medium", 
        "requires_response": True,
        "sentiment": "neutral",
        "action_needed": "reply"
    })
    
    # Mock generate_email_response
    client.generate_email_response = Mock(return_value="Thank you for your email. I'll be happy to help you schedule a meeting for next week. Could you please let me know your availability? Best regards, Michael")
    
    # Mock should_auto_respond
    client.should_auto_respond = Mock(return_value=False)
    
    return client

@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        'id': 'test_email_1',
        'thread_id': 'thread_1',
        'subject': 'Test Email for AI Assistant',
        'sender': 'test@example.com',
        'date': 'Fri, 27 Jun 2025 09:10:25 +0100',
        'body': 'Can you help me schedule a meeting for next week?',
        'snippet': 'Can you help me schedule a meeting for next week?'
    }

@pytest.fixture
def expected_classification():
    """Expected email classification"""
    return {
        "category": "work",
        "priority": "medium",
        "requires_response": True,
        "sentiment": "neutral", 
        "action_needed": "reply"
    }

@pytest.fixture
def expected_response():
    """Expected AI response"""
    return "Thank you for your email. I'll be happy to help you schedule a meeting for next week. Could you please let me know your availability? Best regards, Michael"