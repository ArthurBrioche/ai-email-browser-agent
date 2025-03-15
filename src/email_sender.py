"""
Email sending component for the AI Email Browser Agent.
This module provides functionality to send email responses to users.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailSender:
    """
    A class to handle sending emails via SMTP.
    
    This class connects to Gmail's SMTP server to send emails,
    supporting plain text and HTML content, as well as email threading.
    """
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize the EmailSender with credentials.
        
        Args:
            email_address: The sender's email address
            app_password: The application-specific password for Gmail
        """
        self.email_address = email_address
        self.app_password = app_password
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        
    async def send_email(self, 
                    recipient: str, 
                    subject: str, 
                    body: str, 
                    in_reply_to: Optional[str] = None,
                    references: Optional[str] = None,
                    html_body: Optional[str] = None) -> bool:
        """
        Send an email to a recipient.
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject line
            body: Plain text email body
            in_reply_to: Message ID of the email being replied to (for threading)
            references: Message ID references for conversation threading
            html_body: Optional HTML version of the email body
            
        Returns:
            Boolean indicating if the email was sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.email_address
            message['To'] = recipient
            message['Subject'] = subject
            
            # Include message ID of original email to maintain threading
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
            
            if references:
                message['References'] = references
            elif in_reply_to:  # If no references but we have in_reply_to, use that
                message['References'] = in_reply_to
            
            # Attach plain text body
            message.attach(MIMEText(body, 'plain'))
            
            # Attach HTML body if provided
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Connect to server and send
            logger.info(f"Connecting to SMTP server {self.smtp_server}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.app_password)
            
            logger.info(f"Sending email to {recipient}")
            server.send_message(message)
            server.quit()
            
            logger.info("Email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
            
    async def send_clarification_email(self, 
                                  recipient: str, 
                                  subject: str, 
                                  questions: List[str],
                                  in_reply_to: Optional[str] = None,
                                  references: Optional[str] = None) -> bool:
        """
        Send an email asking for clarification on specific questions.
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject line
            questions: List of questions that need clarification
            in_reply_to: Message ID of the email being replied to
            references: Message ID references for conversation threading
            
        Returns:
            Boolean indicating if the email was sent successfully
        """
        # Create body text with the list of questions
        body = "I need some clarification to better assist you:\n\n"
        for i, question in enumerate(questions, 1):
            body += f"{i}. {question}\n"
        
        body += "\nPlease reply to this email with your answers."
        
        # Create HTML version for better formatting
        html_body = f"""
        <html>
        <body>
            <p>I need some clarification to better assist you:</p>
            <ol>
                {"".join(f"<li>{question}</li>" for question in questions)}
            </ol>
            <p>Please reply to this email with your answers.</p>
        </body>
        </html>
        """
        
        # Prefix subject with "Clarification needed:" if not a reply
        if not in_reply_to:
            subject = f"Clarification needed: {subject}"
        else:
            # Only add "Re:" if it's not already there
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
        
        return await self.send_email(
            recipient=recipient,
            subject=subject,
            body=body,
            in_reply_to=in_reply_to,
            references=references,
            html_body=html_body
        )
        
    async def send_completion_email(self, 
                              recipient: str, 
                              subject: str, 
                              task_summary: str,
                              actions_performed: List[str],
                              in_reply_to: Optional[str] = None,
                              references: Optional[str] = None) -> bool:
        """
        Send a completion email summarizing the task and actions performed.
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject line
            task_summary: Summary of the completed task
            actions_performed: List of actions performed during task execution
            in_reply_to: Message ID of the email being replied to
            references: Message ID references for conversation threading
            
        Returns:
            Boolean indicating if the email was sent successfully
        """
        # Create body text with the task summary and list of actions
        body = f"Task completed! Here's a summary of what I did:\n\n{task_summary}\n\n"
        
        body += "Actions performed:\n"
        for i, action in enumerate(actions_performed, 1):
            body += f"{i}. {action}\n"
        
        body += "\nPlease let me know if you need anything else."
        
        # Create HTML version for better formatting
        html_body = f"""
        <html>
        <body>
            <p><strong>Task completed!</strong> Here's a summary of what I did:</p>
            <p>{task_summary}</p>
            
            <p><strong>Actions performed:</strong></p>
            <ol>
                {"".join(f"<li>{action}</li>" for action in actions_performed)}
            </ol>
            
            <p>Please let me know if you need anything else.</p>
        </body>
        </html>
        """
        
        # Prefix subject with "Completed:" if not a reply
        if not in_reply_to:
            subject = f"Completed: {subject}"
        else:
            # Only add "Re:" if it's not already there
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
        
        return await self.send_email(
            recipient=recipient,
            subject=subject,
            body=body,
            in_reply_to=in_reply_to,
            references=references,
            html_body=html_body
        )