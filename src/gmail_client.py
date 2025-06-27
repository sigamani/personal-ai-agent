import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.settings import settings

SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.compose']

class GmailClient:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        creds = None
        
        if os.path.exists(settings.gmail_token_file):
            with open(settings.gmail_token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(settings.gmail_credentials_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {settings.gmail_credentials_file}. "
                        "Please download from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.gmail_credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(settings.gmail_token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_unread_emails(self, max_results: int = 10) -> List[Dict]:
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self.get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_email_details(self, message_id: str) -> Optional[Dict]:
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])
            
            email_data = {
                'id': message_id,
                'thread_id': message['threadId'],
                'subject': '',
                'sender': '',
                'date': '',
                'body': '',
                'snippet': message.get('snippet', '')
            }
            
            for header in headers:
                name = header['name'].lower()
                if name == 'subject':
                    email_data['subject'] = header['value']
                elif name == 'from':
                    email_data['sender'] = header['value']
                elif name == 'date':
                    email_data['date'] = header['value']
            
            email_data['body'] = self._extract_body(payload)
            
            return email_data
        
        except HttpError as error:
            print(f'An error occurred getting email details: {error}')
            return None
    
    def _extract_body(self, payload) -> str:
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def create_draft_reply(self, original_email: Dict, reply_content: str) -> bool:
        try:
            message = MIMEMultipart()
            message['to'] = original_email['sender']
            message['subject'] = f"Re: {original_email['subject']}"
            
            message.attach(MIMEText(reply_content, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            draft = {
                'message': {
                    'raw': raw_message,
                    'threadId': original_email['thread_id']
                }
            }
            
            self.service.users().drafts().create(
                userId='me',
                body=draft
            ).execute()
            
            return True
        
        except HttpError as error:
            print(f'An error occurred creating draft: {error}')
            return False
    
    def send_reply(self, original_email: Dict, reply_content: str) -> bool:
        try:
            message = MIMEMultipart()
            message['to'] = original_email['sender']
            message['subject'] = f"Re: {original_email['subject']}"
            
            message.attach(MIMEText(reply_content, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            send_message = {
                'raw': raw_message,
                'threadId': original_email['thread_id']
            }
            
            self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()
            
            return True
        
        except HttpError as error:
            print(f'An error occurred sending email: {error}')
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        
        except HttpError as error:
            print(f'An error occurred marking email as read: {error}')
            return False