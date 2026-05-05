"""
SMTP mail helper for HyperVaults.

Sends plain-text emails through Mailpit (a local SMTP catcher) during
development and staging. Never sends real external email — Mailpit captures
everything at SMTP_HOST:SMTP_PORT and makes it visible in its web UI.

In challenge mode, seed emails are injected at startup so players find them
after discovering the exposed Mailpit UI. Each seed group is gated on its own
feature flag so branches can be enabled independently.
"""

import smtplib
import logging
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)

# ----- Second branch: TRACE mail diagnostics -----
_TRACE_SEED_EMAILS = [
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
# Duplicates can still appear after a container restart — noted in README.
_seed_done: bool = False


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
        smtp.sendmail(settings.smtp_from, [to], msg.as_string())


def _try_send(to: str, subject: str, body: str) -> None:
    try:
        send_email(to, subject, body)
        logger.info("Seeded challenge email: %s -> %s", subject, to)
    except Exception as exc:
        # Non-fatal: Mailpit may still be starting up. Restart the backend
        # container if seeded emails are missing from Mailpit.
        logger.warning("Failed to seed email '%s' to %s: %s", subject, to, exc)


def seed_challenge_emails() -> None:
    """Send all enabled challenge seed emails to Mailpit on first call per process.

    Checks each branch flag independently so branches can be mixed freely.
    Called at startup when CHALLENGE_MODE=true.
    """
    global _seed_done
    if _seed_done:
        return
    _seed_done = True

    settings = get_settings()

    # Second branch: TRACE mail diagnostics + exposed Mailpit
    if settings.enable_trace_mail_diagnostics:
        for to, subject, body in _TRACE_SEED_EMAILS:
            _try_send(to, subject, body)

    # Fourth branch: Harbor registry default credentials
    if settings.enable_harbor_default_creds_branch:
        harbor_url = f"http://{settings.harbor_host}"
        body = (
            "Harbor staging registry is online.\n\n"
            f"URL:\n{harbor_url}\n\n"
            "Bootstrap admin:\n"
            "admin / Harbor12345\n\n"
            "TODO before production:\n"
            "- rotate the default Harbor admin password\n"
            "- remove staging-debug image\n"
            "- replace bootstrap admin with scoped robot accounts\n\n"
            # INTENTIONAL CHALLENGE VULNERABILITY: image path leaks credentials and
            # hints at the staging-debug image containing a flag.
            f"Image:\n"
            f"{settings.harbor_host}/hypervaults/hypervaults-api:staging-debug\n"
        )
        _try_send("dev@hypervaults.local", "Harbor staging registry bootstrap", body)
