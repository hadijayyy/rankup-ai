"""
RankUp AI — Notifier
=====================

Sends notifications via email (SMTP) and WhatsApp (placeholder API).
Provides convenience methods for sending weekly reports.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default SMTP settings for Gmail
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# WhatsApp API base URL (placeholder — replace with Twilio/actual provider)
WHATSAPP_API_URL = os.environ.get(
    "WHATSAPP_API_URL",
    "https://api.placeholder-whatsapp.com/v1/messages",
)
WHATSAPP_API_KEY = os.environ.get("WHATSAPP_API_KEY", "")


class Notifier:
    """Send notifications via email, WhatsApp, and other channels.

    Email uses SMTP (Gmail by default). WhatsApp uses a placeholder
    endpoint that should be replaced with a real provider.
    """

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    @staticmethod
    def send_email(
        to: str,
        subject: str,
        html_body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> bool:
        """Send an HTML email via SMTP.

        Args:
            to: Recipient email address (or comma-separated string).
            subject: Email subject line.
            html_body: HTML content for the email body.
            cc: Optional list of CC recipients.
            bcc: Optional list of BCC recipients.

        Returns:
            True if the email was sent successfully, False otherwise.

        Raises:
            RuntimeError: If SMTP credentials are missing.
        """
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            raise RuntimeError(
                "SMTP_EMAIL and SMTP_PASSWORD environment variables must be set "
                "to send emails."
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = SMTP_EMAIL
            msg["To"] = to
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            # Attach plain-text fallback
            plain_text = (
                "This email requires HTML support. "
                "Please view it in an HTML-compatible email client."
            )
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # Build recipient list
            all_recipients = [to]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, all_recipients, msg.as_string())

            logger.info("Email sent to %s (subject: %s)", to, subject)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error(
                "SMTP authentication failed for %s: %s", SMTP_EMAIL, exc
            )
            raise RuntimeError(
                "SMTP authentication failed. Check SMTP_EMAIL and SMTP_PASSWORD."
            ) from exc
        except smtplib.SMTPException as exc:
            logger.error("SMTP error sending to %s: %s", to, exc)
            raise RuntimeError(f"Failed to send email: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected error sending email to %s: %s", to, exc)
            raise RuntimeError(f"Unexpected email error: {exc}") from exc

    # ------------------------------------------------------------------
    # WhatsApp
    # ------------------------------------------------------------------

    @staticmethod
    def send_whatsapp(phone: str, message: str) -> bool:
        """Send a WhatsApp message.

        **This is a placeholder implementation.** Replace the URL and
        logic with your actual WhatsApp Business API or Twilio integration.

        Args:
            phone: Recipient phone number in international format
                (e.g., ``+1234567890``).
            message: Plain-text message content.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not WHATSAPP_API_KEY:
            logger.warning(
                "WHATSAPP_API_KEY is not set. WhatsApp messages are disabled."
            )
            return False

        try:
            # Placeholder: log the message instead of sending
            logger.info(
                "WhatsApp message to %s:\n%s",
                phone,
                message[:200] + ("..." if len(message) > 200 else ""),
            )

            # In production, use:
            # import requests
            # response = requests.post(
            #     WHATSAPP_API_URL,
            #     headers={"Authorization": f"Bearer {WHATSAPP_API_KEY}"},
            #     json={"to": phone, "text": message},
            # )
            # response.raise_for_status()

            logger.info("WhatsApp message queued for %s", phone)
            return True

        except Exception as exc:
            logger.error("Failed to send WhatsApp to %s: %s", phone, exc)
            return False

    # ------------------------------------------------------------------
    # Weekly report convenience
    # ------------------------------------------------------------------

    def send_weekly_report(
        self,
        client_email: str,
        report_data: Dict[str, Any],
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Format and send a weekly report via email (and optionally WhatsApp).

        Args:
            client_email: Recipient email address.
            report_data: Report data dictionary (see
                :meth:`~dashboard.report_formatter.ReportFormatter.format_email_report`).
            phone: Optional phone number for WhatsApp delivery.

        Returns:
            A dict indicating delivery status per channel:
            ``{"email": True/False, "whatsapp": True/False}``.
        """
        from .report_formatter import ReportFormatter

        status: Dict[str, bool] = {"email": False, "whatsapp": False}

        client_name = report_data.get("client_name", "Client")
        report_type = report_data.get("report_type", "weekly").capitalize()
        period = (
            f"{report_data.get('period_start', '')}"
            f" — {report_data.get('period_end', '')}"
        )

        # --- Email ---
        try:
            html_body = ReportFormatter.format_email_report(report_data)
            subject = f"RankUp AI — {report_type} Report for {client_name} ({period})"
            self.send_email(to=client_email, subject=subject, html_body=html_body)
            status["email"] = True
        except Exception as exc:
            logger.error("Failed to send weekly report email: %s", exc)
            status["email"] = False

        # --- WhatsApp ---
        if phone:
            try:
                wa_text = ReportFormatter.format_whatsapp_report(report_data)
                self.send_whatsapp(phone=phone, message=wa_text)
                status["whatsapp"] = True
            except Exception as exc:
                logger.error(
                    "Failed to send weekly report via WhatsApp: %s", exc
                )
                status["whatsapp"] = False
        else:
            logger.info("No phone number provided; skipping WhatsApp delivery.")

        return status


__all__ = ["Notifier"]
