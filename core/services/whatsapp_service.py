"""
WhatsApp messaging service using Twilio
"""
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service to send WhatsApp messages via Twilio"""
    
    def __init__(self):
        """Initialize WhatsApp service with Twilio credentials"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', '')  # Format: whatsapp:+1234567890
        self.enabled = bool(self.account_sid and self.auth_token and self.whatsapp_from)
        
        if not self.enabled:
            logger.warning('WhatsApp service not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_FROM environment variables.')
        
    def send_message(self, to_number: str, message: str) -> bool:
        """
        Send WhatsApp message to a phone number
        Args:
            to_number: Phone number in format +countrycode123456789
            message: Message content
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(f'WhatsApp service disabled. Message not sent to {to_number}')
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Format the recipient number for WhatsApp
            to_whatsapp = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number
            
            msg = client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=to_whatsapp
            )
            
            logger.info(f'WhatsApp message sent to {to_number}. SID: {msg.sid}')
            return True
            
        except ImportError:
            logger.error('Twilio library not installed. Install with: pip install twilio')
            return False
        except Exception as e:
            logger.error(f'Failed to send WhatsApp message to {to_number}: {str(e)}')
            return False
    
    def send_messages_batch(self, recipients: List[dict]) -> dict:
        """
        Send WhatsApp messages to multiple recipients
        Args:
            recipients: List of dicts with 'phone' and 'message' keys
        Returns:
            dict: Results with success/failure counts
        """
        results = {'sent': 0, 'failed': 0, 'errors': []}
        
        for recipient in recipients:
            phone = recipient.get('phone')
            message = recipient.get('message')
            
            if not phone or not message:
                results['failed'] += 1
                results['errors'].append(f'Invalid recipient data: {recipient}')
                continue
            
            if self.send_message(phone, message):
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f'Batch WhatsApp results - Sent: {results["sent"]}, Failed: {results["failed"]}')
        return results


# Singleton instance
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    """Get or create WhatsApp service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
