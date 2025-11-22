"""Email service for sending password reset and notification emails."""

import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        """Initialize email service with SMTP configuration from environment."""
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Legal AI Assistant')

        # Validate configuration
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning(
                "SMTP not configured. Email sending will fail. "
                "Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD environment variables."
            )
        else:
            protocol = "SSL" if self.smtp_use_ssl else "TLS"
            logger.info(f"Email service initialized with SMTP host: {self.smtp_host}:{self.smtp_port} ({protocol})")

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email body
            text_content: Plain text version of email body

        Returns:
            True if email sent successfully, False otherwise
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error("Cannot send email: SMTP not configured")
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email

            # Attach plain text and HTML parts
            part_text = MIMEText(text_content, 'plain')
            part_html = MIMEText(html_content, 'html')
            message.attach(part_text)
            message.attach(part_html)

            # Connect to SMTP server and send
            if self.smtp_use_ssl:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)
            else:
                # Use SMTP with STARTTLS for port 587
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()  # Enable TLS
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        frontend_url: str
    ) -> bool:
        """
        Send password reset email with reset link.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token to include in link
            frontend_url: Base URL of frontend application

        Returns:
            True if email sent successfully, False otherwise
        """
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        subject = "Reset your Legal AI Assistant password"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #fef3c7; color: #1f2937;">
    <div style="max-width: 600px; margin: 40px auto; background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(254, 240, 138, 0.5)); border-radius: 24px; padding: 40px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3);">

        <!-- Logo -->
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; padding: 16px; background: linear-gradient(135deg, rgba(255, 255, 255, 0.6), rgba(254, 240, 138, 0.4)); border-radius: 20px; box-shadow: 0 10px 40px rgba(251, 191, 36, 0.2);">
                <h1 style="margin: 0; font-size: 32px; color: #f59e0b;">⚖️ Cirilla</h1>
            </div>
        </div>

        <!-- Title -->
        <h2 style="color: #78350f; font-size: 24px; font-weight: 700; margin: 0 0 16px 0; text-align: center;">Reset Your Password</h2>

        <!-- Body -->
        <p style="color: #92400e; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
            We received a request to reset your password for your Legal AI Assistant account. Click the button below to create a new password:
        </p>

        <!-- CTA Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #78350f; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4); transition: transform 0.2s;">
                Reset Password
            </a>
        </div>

        <!-- Expiration Notice -->
        <div style="background: rgba(254, 243, 199, 0.6); border-left: 4px solid #f59e0b; padding: 16px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0; color: #92400e; font-size: 14px;">
                ⏰ This link will expire in <strong>15 minutes</strong> for security reasons.
            </p>
        </div>

        <!-- Alternative Link -->
        <p style="color: #78350f; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0;">
            If the button doesn't work, copy and paste this link into your browser:
        </p>
        <p style="color: #92400e; font-size: 13px; word-break: break-all; background: rgba(255, 255, 255, 0.5); padding: 12px; border-radius: 8px; margin: 8px 0 24px 0;">
            {reset_link}
        </p>

        <!-- Security Note -->
        <div style="border-top: 1px solid rgba(251, 191, 36, 0.3); padding-top: 24px; margin-top: 24px;">
            <p style="color: #92400e; font-size: 14px; line-height: 1.6; margin: 0 0 8px 0;">
                <strong>🔒 Security Note:</strong>
            </p>
            <ul style="color: #92400e; font-size: 14px; line-height: 1.6; margin: 0; padding-left: 20px;">
                <li>If you didn't request this password reset, please ignore this email</li>
                <li>Your password won't change unless you click the link above and create a new one</li>
                <li>Never share this link with anyone</li>
            </ul>
        </div>

        <!-- Footer -->
        <p style="color: #a16207; font-size: 13px; text-align: center; margin: 32px 0 0 0;">
            Legal AI Assistant - Your AI-Powered Contract Analysis Platform
        </p>
    </div>
</body>
</html>
"""

        text_content = f"""
Reset Your Password

We received a request to reset your password for your Legal AI Assistant account.

To reset your password, click the following link or copy and paste it into your browser:
{reset_link}

This link will expire in 15 minutes for security reasons.

SECURITY NOTE:
- If you didn't request this password reset, please ignore this email
- Your password won't change unless you click the link above and create a new one
- Never share this link with anyone

---
Legal AI Assistant - Your AI-Powered Contract Analysis Platform
"""

        return self._send_email(to_email, subject, html_content, text_content)

    def send_password_changed_confirmation(
        self,
        to_email: str,
        timestamp: str,
        frontend_url: str
    ) -> bool:
        """
        Send password changed confirmation email.

        Args:
            to_email: Recipient email address
            timestamp: Timestamp when password was changed
            frontend_url: Base URL of frontend application

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Your Legal AI Assistant password was changed"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #fef3c7; color: #1f2937;">
    <div style="max-width: 600px; margin: 40px auto; background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(254, 240, 138, 0.5)); border-radius: 24px; padding: 40px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3);">

        <!-- Logo -->
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; padding: 16px; background: linear-gradient(135deg, rgba(255, 255, 255, 0.6), rgba(254, 240, 138, 0.4)); border-radius: 20px; box-shadow: 0 10px 40px rgba(251, 191, 36, 0.2);">
                <h1 style="margin: 0; font-size: 32px; color: #16a34a;">✓</h1>
            </div>
        </div>

        <!-- Title -->
        <h2 style="color: #78350f; font-size: 24px; font-weight: 700; margin: 0 0 16px 0; text-align: center;">Password Changed Successfully</h2>

        <!-- Body -->
        <p style="color: #92400e; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
            This is a confirmation that the password for your Legal AI Assistant account (<strong>{to_email}</strong>) was changed on <strong>{timestamp}</strong>.
        </p>

        <!-- Security Alert -->
        <div style="background: rgba(254, 243, 199, 0.6); border-left: 4px solid #16a34a; padding: 16px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0 0 8px 0; color: #78350f; font-weight: 600; font-size: 14px;">
                ✓ Your account is now secure with your new password
            </p>
            <p style="margin: 0; color: #92400e; font-size: 14px;">
                All active sessions have been logged out for security.
            </p>
        </div>

        <!-- Unauthorized Change Warning -->
        <div style="background: rgba(254, 226, 226, 0.8); border-left: 4px solid #dc2626; padding: 16px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0 0 8px 0; color: #7f1d1d; font-weight: 600; font-size: 14px;">
                ⚠️ Didn't make this change?
            </p>
            <p style="margin: 0 0 12px 0; color: #991b1b; font-size: 14px; line-height: 1.6;">
                If you did not change your password, your account may have been compromised. Please contact our support team immediately.
            </p>
            <p style="margin: 0; color: #991b1b; font-size: 14px;">
                <strong>Support:</strong> support@legalaiassistant.com
            </p>
        </div>

        <!-- CTA Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{frontend_url}/login" style="display: inline-block; background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #78350f; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);">
                Sign In to Your Account
            </a>
        </div>

        <!-- Footer -->
        <p style="color: #a16207; font-size: 13px; text-align: center; margin: 32px 0 0 0;">
            Legal AI Assistant - Your AI-Powered Contract Analysis Platform
        </p>
    </div>
</body>
</html>
"""

        text_content = f"""
Password Changed Successfully

This is a confirmation that the password for your Legal AI Assistant account ({to_email}) was changed on {timestamp}.

Your account is now secure with your new password. All active sessions have been logged out for security.

DIDN'T MAKE THIS CHANGE?
If you did not change your password, your account may have been compromised. Please contact our support team immediately.

Support: support@legalaiassistant.com

---
Legal AI Assistant - Your AI-Powered Contract Analysis Platform
"""

        return self._send_email(to_email, subject, html_content, text_content)

    def test_connection(self) -> bool:
        """
        Test SMTP connection without sending an email.

        Returns:
            True if connection successful, False otherwise
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error("Cannot test connection: SMTP not configured")
            return False

        try:
            if self.smtp_use_ssl:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)
            else:
                # Use SMTP with STARTTLS for port 587
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
