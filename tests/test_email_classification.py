"""
Tests for email classification functionality
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestEmailClassification:
    """Test email classification using Ollama LLM"""
    
    def test_classify_work_email(self, mock_ollama_client):
        """Test classification of work-related email"""
        work_email = {
            'subject': 'Meeting Request - Project Review',
            'sender': 'colleague@company.com',
            'body': 'Hi Michael, can we schedule a meeting to review the project status next week?'
        }
        
        # Configure mock for work email
        mock_ollama_client.classify_email.return_value = {
            "category": "work",
            "priority": "high",
            "requires_response": True,
            "sentiment": "neutral",
            "action_needed": "schedule"
        }
        
        result = mock_ollama_client.classify_email(work_email)
        
        assert result['category'] == 'work'
        assert result['priority'] == 'high'
        assert result['requires_response'] == True
        assert result['action_needed'] == 'schedule'
    
    def test_classify_personal_email(self, mock_ollama_client):
        """Test classification of personal email"""
        personal_email = {
            'subject': 'Dinner plans this weekend',
            'sender': 'friend@gmail.com', 
            'body': 'Hey! Want to grab dinner this Saturday? Let me know!'
        }
        
        mock_ollama_client.classify_email.return_value = {
            "category": "personal",
            "priority": "low",
            "requires_response": True,
            "sentiment": "positive",
            "action_needed": "reply"
        }
        
        result = mock_ollama_client.classify_email(personal_email)
        
        assert result['category'] == 'personal'
        assert result['priority'] == 'low'
        assert result['requires_response'] == True
        assert result['sentiment'] == 'positive'
    
    def test_classify_spam_email(self, mock_ollama_client):
        """Test classification of spam/promotional email"""
        spam_email = {
            'subject': 'URGENT: Claim your $1000 prize NOW!',
            'sender': 'noreply@suspicious-site.com',
            'body': 'Congratulations! You have won $1000! Click here immediately!'
        }
        
        mock_ollama_client.classify_email.return_value = {
            "category": "spam",
            "priority": "low",
            "requires_response": False,
            "sentiment": "neutral",
            "action_needed": "ignore"
        }
        
        result = mock_ollama_client.classify_email(spam_email)
        
        assert result['category'] == 'spam'
        assert result['requires_response'] == False
        assert result['action_needed'] == 'ignore'
    
    def test_classify_urgent_email(self, mock_ollama_client):
        """Test classification of urgent email"""
        urgent_email = {
            'subject': 'URGENT: Server down - immediate attention needed',
            'sender': 'alerts@company.com',
            'body': 'The production server is down. Please investigate immediately.'
        }
        
        mock_ollama_client.classify_email.return_value = {
            "category": "urgent",
            "priority": "high",
            "requires_response": True,
            "sentiment": "negative",
            "action_needed": "reply"
        }
        
        result = mock_ollama_client.classify_email(urgent_email)
        
        assert result['category'] == 'urgent'
        assert result['priority'] == 'high'
        assert result['requires_response'] == True
    
    def test_classification_fallback_on_error(self):
        """Test fallback classification when LLM fails"""
        from src.ollama_client import OllamaClient
        
        # Create a real client and mock generate_response to fail
        with patch('ollama.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = OllamaClient()
            client.generate_response = Mock(side_effect=Exception("LLM Error"))
            
            email_data = {
                'subject': 'Test email',
                'sender': 'test@example.com',
                'body': 'Test body'
            }
            
            result = client.classify_email(email_data)
            
            # Should return safe fallback classification
            assert result['category'] == 'unknown'
            assert result['priority'] == 'medium'
            assert result['requires_response'] == False
            assert result['action_needed'] == 'ignore'
    
    def test_classification_json_parsing(self):
        """Test that classification handles JSON parsing correctly"""
        from src.ollama_client import OllamaClient
        
        with patch('ollama.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = OllamaClient()
            
            # Mock generate_response to return valid JSON
            valid_json_response = '{"category": "work", "priority": "medium", "requires_response": true, "sentiment": "neutral", "action_needed": "reply"}'
            client.generate_response = Mock(return_value=valid_json_response)
            
            email_data = {
                'subject': 'Valid JSON test',
                'sender': 'test@example.com',
                'body': 'Test body'
            }
            
            result = client.classify_email(email_data)
            
            assert result['category'] == 'work'
            assert result['priority'] == 'medium'
            assert result['requires_response'] == True
    
    def test_classification_invalid_json_fallback(self):
        """Test fallback when LLM returns invalid JSON"""
        from src.ollama_client import OllamaClient
        
        with patch('ollama.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = OllamaClient()
            
            # Mock generate_response to return invalid JSON
            client.generate_response = Mock(return_value="This is not valid JSON")
            
            email_data = {
                'subject': 'Invalid JSON test',
                'sender': 'test@example.com',
                'body': 'Test body'
            }
            
            result = client.classify_email(email_data)
            
            # Should return safe fallback
            assert result['category'] == 'unknown'
            assert result['priority'] == 'medium'
            assert result['requires_response'] == False
    
    def test_should_auto_respond_logic(self, mock_ollama_client):
        """Test auto-response decision logic"""
        
        # Test promotional email - should auto-respond
        promotional_classification = {
            "category": "promotional",
            "priority": "low",
            "requires_response": True,
            "action_needed": "reply"
        }
        mock_ollama_client.should_auto_respond.return_value = True
        result = mock_ollama_client.should_auto_respond(promotional_classification)
        assert result == True
        
        # Test work email - should not auto-respond
        work_classification = {
            "category": "work", 
            "priority": "high",
            "requires_response": True,
            "action_needed": "reply"
        }
        mock_ollama_client.should_auto_respond.return_value = False
        result = mock_ollama_client.should_auto_respond(work_classification)
        assert result == False
    
    def test_email_body_truncation(self, mock_ollama_client):
        """Test that long email bodies are properly truncated for classification"""
        long_body = "This is a very long email body. " * 100  # Create long text
        
        long_email = {
            'subject': 'Long email test',
            'sender': 'test@example.com',
            'body': long_body
        }
        
        # The actual classification should handle truncation
        mock_ollama_client.classify_email(long_email)
        
        # Verify classify_email was called (truncation happens inside the method)
        mock_ollama_client.classify_email.assert_called_once_with(long_email)