"""Validación de JWT. Aún en desarrollo (AUTH_ENABLED=false) y se asume como que estamos usando un usuario de prueba."""
import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
JWKS_URL = os.getenv("JWKS_URL", "")
ISSUER = os.getenv("OIDC_ISSUER") or None

_bearer = HTTPBearer(auto_error=False)
_jwks = PyJWKClient(JWKS_URL) if AUTH_ENABLED and JWKS_URL else None


def get_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if not AUTH_ENABLED:
        return "dev-user"
    if not cred or not _jwks:
        raise HTTPException(401, "Falta el token de autenticación")
    try:
        key = _jwks.get_signing_key_from_jwt(cred.credentials).key
        claims = jwt.decode(cred.credentials, key, algorithms=["RS256"],
                            issuer=ISSUER, options={"verify_aud": False})
    except Exception:
        raise HTTPException(401, "Token inválido o vencido")
    return claims.get("preferred_username") or claims.get("email") or claims["sub"]
