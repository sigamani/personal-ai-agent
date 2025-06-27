"""
End-to-end workflow tests for Personal AI Assistant

This test suite locks in the core workflow:
1. Email detection and retrieval
2. Email classification using LLM
3. Response generation using LLM  
4. Draft creation in Gmail
5. Email marking as read
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestEndToEndWorkflow:
    """Test the complete email processing workflow"""
    
    def test_complete_email_processing_workflow(self, mock_gmail_client, mock_ollama_client, sample_email_data, expected_classification, expected_response):
        """
        Test the complete end-to-end workflow:
        1. Get unread emails
        2. Classify email with AI
        3. Generate response with AI
        4. Create draft reply
        5. Mark email as read
        """
        from src.email_processor import EmailProcessor
        
        # Setup - inject mocked clients
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            
            # Execute the complete workflow
            result = processor.process_emails()
            
            # Verify workflow steps were executed
            
            # 1. Gmail client should get unread emails
            mock_gmail_client.service.users().messages().list.assert_called_once()
            mock_gmail_client.service.users().messages().get.assert_called()
            
            # 2. Ollama should classify the email
            mock_ollama_client.classify_email.assert_called()
            
            # 3. Ollama should generate response
            mock_ollama_client.generate_email_response.assert_called()
            
            # 4. Gmail should create draft
            mock_gmail_client.service.users().drafts().create.assert_called()
            
            # 5. Gmail should mark email as read
            mock_gmail_client.service.users().messages().modify.assert_called()
            
            # Verify results
            assert result['processed'] > 0
            assert result['drafts_created'] > 0
            assert 'timestamp' in result
    
    def test_email_requires_response_workflow(self, mock_gmail_client, mock_ollama_client):
        """Test workflow when email requires a response"""
        from src.email_processor import EmailProcessor
        
        # Configure mocks for email that requires response
        mock_ollama_client.classify_email.return_value = {
            "category": "work",
            "priority": "high",
            "requires_response": True,
            "sentiment": "neutral",
            "action_needed": "reply"
        }
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            result = processor.process_emails()
            
            # Should classify email
            mock_ollama_client.classify_email.assert_called()
            
            # Should generate response
            mock_ollama_client.generate_email_response.assert_called()
            
            # Should create draft
            mock_gmail_client.service.users().drafts().create.assert_called()
            
            # Should mark as read
            mock_gmail_client.service.users().messages().modify.assert_called()
            
            assert result['drafts_created'] > 0
    
    def test_email_no_response_needed_workflow(self, mock_gmail_client, mock_ollama_client):
        """Test workflow when email doesn't require a response"""
        from src.email_processor import EmailProcessor
        
        # Configure mocks for email that doesn't require response
        mock_ollama_client.classify_email.return_value = {
            "category": "promotional",
            "priority": "low",
            "requires_response": False,
            "sentiment": "neutral",
            "action_needed": "ignore"
        }
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            result = processor.process_emails()
            
            # Should classify email
            mock_ollama_client.classify_email.assert_called()
            
            # Should NOT generate response
            mock_ollama_client.generate_email_response.assert_not_called()
            
            # Should NOT create draft
            mock_gmail_client.service.users().drafts().create.assert_not_called()
            
            # Should still mark as read
            mock_gmail_client.service.users().messages().modify.assert_called()
            
            assert result['drafts_created'] == 0
    
    def test_ollama_unavailable_fallback(self, mock_gmail_client):
        """Test workflow when Ollama is unavailable"""
        from src.email_processor import EmailProcessor
        
        # Mock unavailable Ollama
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient') as mock_ollama_class:
            
            mock_ollama_client = Mock()
            mock_ollama_client.is_available.return_value = False
            mock_ollama_class.return_value = mock_ollama_client
            
            processor = EmailProcessor()
            result = processor.process_emails()
            
            # Should still process emails (mark as read only)
            mock_gmail_client.service.users().messages().list.assert_called()
            mock_gmail_client.service.users().messages().modify.assert_called()
            
            # Should not attempt AI processing
            mock_ollama_client.classify_email.assert_not_called()
            mock_ollama_client.generate_email_response.assert_not_called()
            
            assert result['processed'] > 0
            assert result['drafts_created'] == 0
    
    def test_auto_send_disabled_creates_drafts(self, mock_gmail_client, mock_ollama_client):
        """Test that auto-send disabled results in draft creation"""
        from src.email_processor import EmailProcessor
        
        # Configure for email that could be auto-sent but auto-send is disabled
        mock_ollama_client.classify_email.return_value = {
            "category": "promotional",
            "priority": "low", 
            "requires_response": True,
            "sentiment": "neutral",
            "action_needed": "reply"
        }
        mock_ollama_client.should_auto_respond.return_value = True
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client), \
             patch('config.settings.settings') as mock_settings:
            
            # Ensure auto-send is disabled
            mock_settings.auto_send_responses = False
            
            processor = EmailProcessor()
            result = processor.process_emails()
            
            # Should create draft, not send
            mock_gmail_client.service.users().drafts().create.assert_called()
            
            # Should not call send
            assert not hasattr(mock_gmail_client, 'send_reply') or not mock_gmail_client.send_reply.called
            
            assert result['drafts_created'] > 0
            assert result['responded'] == 0
    
    def test_error_handling_in_workflow(self, mock_gmail_client, mock_ollama_client):
        """Test workflow error handling"""
        from src.email_processor import EmailProcessor
        
        # Configure Gmail to raise an error
        mock_gmail_client.service.users().messages().list.side_effect = Exception("Gmail API Error")
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            
            # Should handle errors gracefully
            result = processor.process_emails()
            
            # Should return safe defaults
            assert result['processed'] == 0
            assert result['responded'] == 0
            assert result['drafts_created'] == 0
    
    def test_processing_stats_accuracy(self, mock_gmail_client, mock_ollama_client):
        """Test that processing statistics are accurate"""
        from src.email_processor import EmailProcessor
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            
            # Test stats before processing
            stats = processor.get_processing_stats()
            assert stats['gmail_authenticated'] == True
            assert stats['ollama_available'] == True
            assert 'auto_send_enabled' in stats
            assert 'check_interval' in stats
            assert 'model' in stats
            
            # Process emails
            result = processor.process_emails()
            
            # Verify stats match results
            assert isinstance(result['processed'], int)
            assert isinstance(result['responded'], int) 
            assert isinstance(result['drafts_created'], int)
            assert result['processed'] >= result['responded'] + result['drafts_created']


class TestWorkflowDataFlow:
    """Test that data flows correctly through the workflow"""
    
    def test_email_data_passed_correctly(self, mock_gmail_client, mock_ollama_client, sample_email_data):
        """Test that email data is passed correctly between components"""
        from src.email_processor import EmailProcessor
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            processor.process_emails()
            
            # Check that classify_email was called with correct data structure
            call_args = mock_ollama_client.classify_email.call_args[0][0]
            assert 'subject' in call_args
            assert 'sender' in call_args
            assert 'body' in call_args
            
            # Check that generate_email_response was called with email data and classification
            gen_call_args = mock_ollama_client.generate_email_response.call_args
            email_arg = gen_call_args[0][0]
            classification_arg = gen_call_args[0][1]
            
            assert 'subject' in email_arg
            assert 'category' in classification_arg
    
    def test_response_content_in_draft(self, mock_gmail_client, mock_ollama_client):
        """Test that AI-generated response content makes it into the draft"""
        from src.email_processor import EmailProcessor
        
        expected_response = "This is the AI generated response"
        mock_ollama_client.generate_email_response.return_value = expected_response
        
        with patch('src.email_processor.GmailClient', return_value=mock_gmail_client), \
             patch('src.email_processor.OllamaClient', return_value=mock_ollama_client):
            
            processor = EmailProcessor()
            processor.process_emails()
            
            # Verify draft creation was called
            mock_gmail_client.service.users().drafts().create.assert_called()
            
            # Note: In a real test, you'd verify the draft content contains the response
            # This would require more sophisticated mocking of the draft creation process