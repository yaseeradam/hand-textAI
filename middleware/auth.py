import uuid
from fastapi import Request, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)

async def verify_client_key(
    request: Request,
    header_key: str | None = Security(api_key_header),
    bearer_creds: HTTPAuthorizationCredentials | None = Security(bearer_auth),
) -> str | None:
    """
    Validates client authentication.
    Checks:
    1. X-API-Key header
    2. Authorization: Bearer <token>
    3. ?api_key query param
    """
    # 1. Unrestricted mode
    if "*" in settings.ALLOWED_API_KEYS:
        return "public_access"

    provided_key = header_key

    if not provided_key and bearer_creds:
        provided_key = bearer_creds.credentials

    if not provided_key:
        provided_key = request.query_params.get("api_key")

    if not settings.is_client_authorized(provided_key):
        request_id = str(uuid.uuid4())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "unauthorized",
                "message": "Invalid or missing API key. Supply your key via 'X-API-Key' or 'Authorization: Bearer <token>'.",
                "request_id": request_id,
            },
        )

    return provided_key
