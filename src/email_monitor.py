"""
Email monitoring component for the AI Email Browser Agent.
This module provides functionality to monitor a Gmail inbox for new messages.
"""

import asyncio
import imaplib
import email
from email.header import decode_header
import logging
import time
from typing import Callable, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailMonitor:
    """
    A class to monitor an email inbox for new messages using IMAP.
    
    This class connects to a Gmail inbox using IMAP and continuously 
    checks for new (unread) emails. When a new email is found, it 
    extracts the email content and passes it to a callback function.
    """
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize the EmailMonitor with credentials.
        
        Args:
            email_address: The email address to monitor
            app_password: The application-specific password for Gmail
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = 'imap.gmail.com'
        self.is_running = False
        
    async def start_monitoring(self, callback: Callable[[Dict[str, Any]], Any], 
                                check_interval: int = 30):
        """
        Start monitoring the inbox for new emails.
        
        Args:
            callback: Function to call when a new email is received
            check_interval: Time in seconds between inbox checks
        """
        self.is_running = True
        logger.info(f"Starting email monitoring for {self.email_address}")
        
        while self.is_running:
            try:
                # Connect to the IMAP server
                mail = imaplib.IMAP4_SSL(self.imap_server)
                mail.login(self.email_address, self.app_password)
                mail.select('inbox')
                
                # Search for unread emails
                status, messages = mail.search(None, '(UNSEEN)')
                
                if status == 'OK' and messages[0]:
                    logger.info(f"Found {len(messages[0].split())} new email(s)")
                    
                    for num in messages[0].split():
                        # Process new email
                        status, data = mail.fetch(num, '(RFC822)')
                        email_message = email.message_from_bytes(data[0][1])
                        
                        # Extract email details
                        subject = self._decode_header_value(email_message.get("Subject", ""))
                        sender = self._decode_header_value(email_message.get("From", ""))
                        message_id = email_message.get("Message-ID", "")
                        in_reply_to = email_message.get("In-Reply-To", "")
                        references = email_message.get("References", "")
                        
                        # Extract body
                        body = self._extract_email_body(email_message)
                        
                        # Pass to callback for processing
                        await callback({
                            "message_id": message_id,
                            "in_reply_to": in_reply_to,
                            "references": references,
                            "subject": subject,
                            "sender": sender,
                            "body": body,
                            "raw_email": email_message
                        })
                
                # Safely close the connection
                mail.close()
                mail.logout()
            except Exception as e:
                logger.error(f"Error monitoring emails: {e}")
            
            # Check every interval seconds
            await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop the email monitoring process."""
        self.is_running = False
        logger.info("Email monitoring stopped")
    
    def _decode_header_value(self, header_value: str) -> str:
        """
        Decode email header values that might be encoded.
        
        Args:
            header_value: The header value to decode
        
        Returns:
            Decoded header value as string
        """
        if not header_value:
            return ""
            
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                if encoding:
                    decoded_parts.append(part.decode(encoding))
                else:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        
        return ''.join(str(part) for part in decoded_parts)
    
    def _extract_email_body(self, email_message) -> str:
        """
        Extract the body text from an email message.
        
        Args:
            email_message: The email message to extract from
            
        Returns:
            The extracted body text
        """
        body = ""
        
        if email_message.is_multipart():
            # Handle multipart messages
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    # Plain text is preferred
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break
                elif content_type == "text/html" and not body:
                    # Use HTML if no plain text is found
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        # In a real implementation, you might want to convert HTML to plain text here
        else:
            # Handle non-multipart messages
            payload = email_message.get_payload(decode=True)
            if payload:
                charset = email_message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        
        return body