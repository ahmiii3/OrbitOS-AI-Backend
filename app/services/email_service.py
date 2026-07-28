import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import aiosmtplib
from app.core.config import settings
from app.email import render_forgot_password_template, render_verify_email_template

logger = logging.getLogger(__name__)


class EmailService:
    """Service responsible for rendering templates and sending emails asynchronously via SMTP."""

    async def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Send an HTML email using SMTP."""
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        try:
            if settings.SMTP_SSL:
                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER or None,
                    password=settings.SMTP_PASSWORD or None,
                    use_tls=True,
                )
            elif settings.SMTP_TLS:
                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER or None,
                    password=settings.SMTP_PASSWORD or None,
                    start_tls=True,
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER or None,
                    password=settings.SMTP_PASSWORD or None,
                )
            logger.info(f"Successfully sent email '{subject}' to {to_email}")
        except Exception as exc:
            logger.warning(
                f"SMTP delivery failed for '{subject}' to {to_email} (Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}). Error: {exc}. "
                f"[DEVELOPMENT FALLBACK LOG] Email Content:\nSubject: {subject}\nTo: {to_email}\nBody: {html_content[:500]}..."
            )
            # In testing/dev environments without an active SMTP daemon, log gracefully rather than failing the transaction

    async def send_verification_email(self, to_email: str, name: str, code: str) -> None:
        """Render verification template with 6-digit code and send email."""
        html_content = render_verify_email_template(name=name, code=code)
        await self.send_email(
            to_email=to_email,
            subject="Your OrbitOS AI verification code",
            html_content=html_content,
        )

    async def send_password_reset_email(self, to_email: str, name: str, token: str) -> None:
        """Render forgot password template and send email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        html_content = render_forgot_password_template(name=name, reset_url=reset_url)
        await self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Enterprise SaaS",
            html_content=html_content,
        )
