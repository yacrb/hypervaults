from fastapi import FastAPI, HTTPException, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.config import get_settings


settings = get_settings()

LOCALHOST_VALUES = {"127.0.0.1", "::1", "localhost"}
DOCS_BYPASS_FLAG = "flag{trusted_proxy_headers_are_not_user_input}"


def is_request_from_localhost(request: Request) -> bool:
    client_host = request.client.host if request.client else ""

    if settings.enable_x_forwarded_docs_bypass:
        # INTENTIONAL CHALLENGE VULNERABILITY:
        # This trusts a user-controlled forwarding header and treats spoofed
        # localhost values as internal traffic. Keep this behavior limited to
        # ENABLE_X_FORWARDED_DOCS_BYPASS=true.
        forwarded_for = request.headers.get("x-forwarded-for", "")
        forwarded_hosts = {part.strip() for part in forwarded_for.split(",") if part.strip()}
        if forwarded_hosts.intersection({"127.0.0.1", "::1"}):
            return True

    # Secure/default behavior: use the socket peer only, not proxy headers.
    return client_host in LOCALHOST_VALUES


def require_localhost_docs_access(request: Request) -> None:
    if not is_request_from_localhost(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API documentation is restricted to localhost",
        )


def openapi_description() -> str:
    if settings.challenge_mode or settings.enable_x_forwarded_docs_bypass:
        return f"Internal documentation. Access should be restricted to localhost. {DOCS_BYPASS_FLAG}"
    return "Secure document vault API. Interactive documentation is restricted to localhost/internal access."


def register_docs_routes(app: FastAPI) -> None:
    @app.get("/api/docs", include_in_schema=False)
    def swagger_docs(request: Request) -> HTMLResponse:
        require_localhost_docs_access(request)
        return get_swagger_ui_html(
            openapi_url="/api/openapi.json",
            title="HyperVaults API Docs",
        )

    @app.get("/api/openapi.json", include_in_schema=False)
    def openapi_json(request: Request) -> dict:
        require_localhost_docs_access(request)
        return app.openapi()

    @app.get("/api/redoc", include_in_schema=False)
    def redoc(request: Request) -> HTMLResponse:
        require_localhost_docs_access(request)
        return get_redoc_html(
            openapi_url="/api/openapi.json",
            title="HyperVaults API ReDoc",
        )
