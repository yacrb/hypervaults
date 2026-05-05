"""
SMTP mail helper for HyperVaults.

Sends plain-text emails through Mailpit (a local SMTP catcher) during
development and staging. Never sends real external email — Mailpit captures
everything at SMTP_HOST:SMTP_PORT and makes it visible in its web UI.

In challenge mode, seed emails are injected at startup to give players
something to find after discovering the exposed Mailpit UI.
"""

import smtplib
import logging
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)

_SEED_EMAILS = [
    (
        "test.user@hypervaults.local",
        "Welcome to HyperVaults",
        (
            "Welcome to HyperVaults.\n\n"
            "This is a staging mailbox test used by the HyperVaults team.\n"
        ),
    ),
    (
        "support@hypervaults.local",
        "HyperVaults Mail Diagnostic",
        (
            "The development mailbox was reachable through the edge proxy.\n\n"
            "flag{dev_mailboxes_do_not_belong_in_prod}\n"
        ),
    ),
    (
        "dev@hypervaults.local",
        "Staging dev account",
        (
            "Temporary dev account for QA:\n\n"
            "Email: dev@hypervaults.local\n"
            "Password: DevVaults2026!\n\n"
            "Reminder: remove this before production.\n"
        ),
    ),
]

# In-memory guard so seed emails are sent only once per process lifetime.
# Duplicates can still appear after a container restart — this is noted in the README.
_seed_done: bool = False


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
        smtp.sendmail(settings.smtp_from, [to], msg.as_string())


def seed_challenge_emails() -> None:
    """Send staging seed emails to Mailpit on first call per process.

    Called at startup when CHALLENGE_MODE=true and
    ENABLE_TRACE_MAIL_DIAGNOSTICS=true. Silently skips if Mailpit is
    unreachable so backend startup does not fail.
    """
    global _seed_done
    if _seed_done:
        return
    _seed_done = True

    for to, subject, body in _SEED_EMAILS:
        try:
            send_email(to, subject, body)
            logger.info("Seeded challenge email: %s → %s", subject, to)
        except Exception as exc:
            # Non-fatal: Mailpit may still be starting up. Players can retry
            # by restarting the backend container if emails are missing.
            logger.warning("Failed to seed email '%s' to %s: %s", subject, to, exc)
