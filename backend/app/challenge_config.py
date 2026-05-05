from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from app.config import get_settings


SECRETS_DIR = Path("/run/secrets")


def _read_secret_file(secret_name: str) -> str | None:
    path = SECRETS_DIR / secret_name
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not value:
        return None
    return value


def _secret_or_env(secret_name: str, env_name: str, default: str) -> str:
    return _read_secret_file(secret_name) or os.getenv(env_name) or default


@dataclass(frozen=True)
class ChallengeConfig:
    docs_bypass_flag: str
    trace_mail_flag: str
    mailpit_inbox_flag: str
    minio_public_bucket_flag: str
    harbor_debug_image_flag: str
    mailpit_basic_user: str
    mailpit_basic_password: str
    harbor_admin_user: str
    harbor_admin_password: str


@lru_cache
def get_challenge_config() -> ChallengeConfig:
    settings = get_settings()
    return ChallengeConfig(
        docs_bypass_flag=_secret_or_env(
            "flag_docs_bypass",
            "FLAG_DOCS_BYPASS",
            "flag{trusted_proxy_headers_are_not_user_input}",
        ),
        trace_mail_flag=_secret_or_env(
            "flag_trace_mail",
            "FLAG_TRACE_MAIL",
            "flag{trace_mail_diagnostics_exposed}",
        ),
        mailpit_inbox_flag=_secret_or_env(
            "flag_mailpit_inbox",
            "FLAG_MAILPIT_INBOX",
            "flag{dev_mailboxes_do_not_belong_in_prod}",
        ),
        minio_public_bucket_flag=_secret_or_env(
            "flag_minio_public_bucket",
            "FLAG_MINIO_PUBLIC_BUCKET",
            "flag{public_buckets_make_private_uploads_public}",
        ),
        harbor_debug_image_flag=_secret_or_env(
            "flag_harbor_debug_image",
            "FLAG_HARBOR_DEBUG_IMAGE",
            "flag{debug_images_should_not_reach_prod_registries}",
        ),
        mailpit_basic_user=_secret_or_env("mailpit_basic_user", "MAILPIT_BASIC_USER", settings.mailpit_basic_user),
        mailpit_basic_password=_secret_or_env(
            "mailpit_basic_password",
            "MAILPIT_BASIC_PASSWORD",
            settings.mailpit_basic_password,
        ),
        harbor_admin_user=_secret_or_env("harbor_admin_user", "HARBOR_ADMIN_USER", settings.harbor_admin_user),
        harbor_admin_password=_secret_or_env(
            "harbor_admin_password",
            "HARBOR_ADMIN_PASSWORD",
            settings.harbor_admin_password,
        ),
    )
