"""
SMTP mail helper for HyperVaults.

Sends plain-text emails through Mailpit (a local SMTP catcher) during
development and staging. Never sends real external email — Mailpit captures
everything at SMTP_HOST:SMTP_PORT and makes it visible in its web UI.

In challenge mode, seed emails are kept present in Mailpit so players can still
recover the chain if another player deletes shared mailbox entries.
"""

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from app.challenge_config import get_challenge_config
from app.config import get_settings

logger = logging.getLogger(__name__)

_startup_fallback_sent: bool = False


def _trace_seed_emails(mailpit_inbox_flag: str) -> list[tuple[str, str, str]]:
    return [
        (
            "test.user@hypervaults.local",
            "Welcome to HyperVaults staging",
            (
                "Welcome to the HyperVaults staging environment.\n\n"
                "This mailbox confirms local SMTP capture is working for QA sign-up tests.\n"
            ),
        ),
        (
            "qa@hypervaults.local",
            "Password reset test for QA",
            (
                "A password reset template test was triggered for qa@hypervaults.local.\n\n"
                "No real reset token is included in this staging message.\n"
            ),
        ),
        (
            "support@hypervaults.local",
            "Mail diagnostic warning",
            (
                "The development mailbox was reachable through the edge proxy during staging validation.\n\n"
                f"{mailpit_inbox_flag}\n"
            ),
        ),
        (
            "dev@hypervaults.local",
            "Reminder to remove debug services before launch",
            (
                "Reminder for the release checklist:\n\n"
                "- remove exposed mail diagnostics\n"
                "- disable public object gateway\n"
                "- rotate all staging-only credentials\n"
            ),
        ),
    ]


def _enabled_seed_emails() -> list[tuple[str, str, str]]:
    settings = get_settings()
    challenge_config = get_challenge_config()
    emails: list[tuple[str, str, str]] = []

    # Second branch: TRACE mail diagnostics + exposed Mailpit
    if settings.enable_trace_mail_diagnostics:
        emails.extend(_trace_seed_emails(challenge_config.mailpit_inbox_flag))

    # Fourth branch: Harbor registry default credentials
    if settings.enable_harbor_default_creds_branch:
        harbor_url = f"https://{settings.harbor_host}"
        body = (
            "Harbor staging registry is online.\n\n"
            f"URL:\n{harbor_url}\n\n"
            "Bootstrap admin:\n"
            f"{challenge_config.harbor_admin_user} / {challenge_config.harbor_admin_password}\n\n"
            "TODO before production:\n"
            "- rotate the default Harbor admin password\n"
            "- remove staging-debug image\n"
            "- replace bootstrap admin with scoped robot accounts\n\n"
            # INTENTIONAL CHALLENGE VULNERABILITY: image path leaks credentials and
            # hints at the staging-debug image containing a flag.
            f"Image:\n"
            f"{settings.harbor_host}/hypervaults/hypervaults-api:staging-debug\n"
        )
        emails.append(("dev@hypervaults.local", "Harbor staging registry bootstrap", body))

    return emails


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
        # Non-fatal: Mailpit may still be starting up. The periodic reseed loop
        # will try again without failing the backend process.
        logger.warning("Failed to seed email '%s' to %s: %s", subject, to, exc)


def _mailpit_subjects() -> set[str] | None:
    settings = get_settings()
    try:
        response = httpx.get(settings.mailpit_api_url, params={"limit": 1000}, timeout=3.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Failed to query Mailpit messages for reseed check: %s", exc)
        return None

    messages = payload.get("messages") or payload.get("Messages") or []
    subjects: set[str] = set()
    for message in messages:
        subject = message.get("Subject") or message.get("subject")
        if isinstance(subject, str):
            subjects.add(subject)
    return subjects


def ensure_challenge_emails() -> None:
    """Send any enabled seed emails missing from Mailpit.

    The check is subject-based because each seeded challenge email has a stable,
    unique subject. If Mailpit's API is temporarily unavailable at startup, send
    one compatibility seed pass, then wait for the API before future reseeds.
    """
    global _startup_fallback_sent
    desired_emails = _enabled_seed_emails()
    if not desired_emails:
        return

    existing_subjects = _mailpit_subjects()
    if existing_subjects is None:
        if not _startup_fallback_sent:
            _startup_fallback_sent = True
            for to, subject, body in desired_emails:
                _try_send(to, subject, body)
        return

    for to, subject, body in desired_emails:
        if subject not in existing_subjects:
            _try_send(to, subject, body)


async def reseed_challenge_emails_forever() -> None:
    settings = get_settings()
    while True:
        await asyncio.sleep(settings.mailpit_reseed_interval_seconds)
        await asyncio.to_thread(ensure_challenge_emails)
