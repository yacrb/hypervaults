"""
INTENTIONAL CHALLENGE VULNERABILITY (second branch — OWASP A02 Security Misconfiguration):

TRACE /api/diagnostics/mail leaks development mail infrastructure details including
Mailpit credentials and the dev account hint. This route is only registered when
ENABLE_TRACE_MAIL_DIAGNOSTICS=true.

Expected player path:
  1. Use X-Forwarded-For: 127.0.0.1 to access /api/docs (first vuln)
  2. Notice TRACE /api/diagnostics/mail in the OpenAPI schema
  3. curl -X TRACE http://localhost/api/diagnostics/mail -H "X-Forwarded-For: 127.0.0.1"
  4. Receive Mailpit credentials and the TRACE mail flag
  5. Visit http://localhost/mailpit with the leaked credentials
  6. Read the seeded Mailpit flag email
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.challenge_config import get_challenge_config
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api", tags=["internal-diagnostics"])

# INTENTIONAL CHALLENGE VULNERABILITY:
# TRACE endpoint leaks Mailpit credentials and internal mail infrastructure.
# The "environment: production" label is intentionally wrong — this is staging/dev
# infrastructure masquerading as production config, which is the misconfiguration.
@router.api_route(
    "/diagnostics/mail",
    methods=["TRACE"],
    summary="Mail diagnostics",
    description="Internal mail diagnostics endpoint used during staging.",
    response_class=JSONResponse,
)
def trace_mail_diagnostics() -> dict:
    challenge_config = get_challenge_config()
    return {
        "service": "hypervaults-api",
        "component": "mail",
        "environment": "production",
        "diagnostic_mode": True,
        "mail_provider": "mailpit",
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "mail_ui": settings.mailpit_ui_public_url,
        "mail_ui_auth": {
            "type": "basic",
            "username": challenge_config.mailpit_basic_user,
            "password": challenge_config.mailpit_basic_password,
        },
        "dev_account": {
            "email": "dev@hypervaults.local",
            "note": "Temporary dev mailbox account used during staging tests",
        },
        "note": "Mail diagnostics should never expose development infrastructure or credentials.",
        "flag": challenge_config.trace_mail_flag,
    }
