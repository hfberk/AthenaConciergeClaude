"""Amazon SES email integration"""

import email
from email import policy
from email.parser import BytesParser
import boto3
from bs4 import BeautifulSoup
import structlog

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class SESIntegration:
    """Handles Amazon SES email processing"""

    def __init__(self):
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("AWS credentials not configured, SES integration disabled")
            self.ses_client = None
            self.s3_client = None
            return

        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

    def process_inbound_email(self, sns_message: dict):
        """
        Process inbound email from SES/SNS notification.

        SES stores the email in S3 and sends an SNS notification
        with the S3 location. This method retrieves and processes it.
        """
        try:
            # Extract S3 location from SNS message
            mail = sns_message.get("mail", {})
            message_id = mail.get("messageId")

            logger.info("Processing inbound email", message_id=message_id)

            # TODO: Retrieve email from S3
            # bucket = "your-ses-bucket"
            # key = f"emails/{message_id}"
            # response = self.s3_client.get_object(Bucket=bucket, Key=key)
            # email_content = response['Body'].read()

            # Parse email
            # parsed_email = self._parse_email(email_content)

            # Look up person by email address
            # Match to comm_identity
            # Create/update conversation
            # Process with orchestrator agent
            # Send reply via SES

            logger.info("Email processed successfully")

        except Exception as e:
            logger.error("Error processing inbound email", error=str(e), exc_info=True)
            raise

    def _parse_email(self, email_bytes: bytes) -> dict:
        """Parse raw email bytes into structured format"""
        msg = BytesParser(policy=policy.default).parsebytes(email_bytes)

        # Extract headers
        from_address = msg.get('From')
        to_address = msg.get('To')
        subject = msg.get('Subject')
        message_id = msg.get('Message-ID')
        in_reply_to = msg.get('In-Reply-To')
        references = msg.get('References')

        # Extract body
        text_content = ""
        html_content = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    text_content = part.get_content()
                elif content_type == "text/html":
                    html_content = part.get_content()
        else:
            if msg.get_content_type() == "text/plain":
                text_content = msg.get_content()
            elif msg.get_content_type() == "text/html":
                html_content = msg.get_content()

        # Convert HTML to plain text if needed
        if not text_content and html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator='\n', strip=True)

        return {
            "from": from_address,
            "to": to_address,
            "subject": subject,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references,
            "text_content": text_content,
            "html_content": html_content
        }

    def send_email(self, to_address: str, subject: str, body_text: str, body_html: str = None):
        """Send email via SES"""
        if not self.ses_client:
            logger.warning("SES client not initialized")
            return

        try:
            destination = {'ToAddresses': [to_address]}

            message = {
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text}
                }
            }

            if body_html:
                message['Body']['Html'] = {'Data': body_html}

            response = self.ses_client.send_email(
                Source=settings.ses_email,
                Destination=destination,
                Message=message
            )

            logger.info("Email sent successfully",
                       message_id=response['MessageId'],
                       to=to_address)

            return response['MessageId']

        except Exception as e:
            logger.error("Error sending email", error=str(e), exc_info=True)
            raise


# Create singleton instance
ses_integration = SESIntegration()
