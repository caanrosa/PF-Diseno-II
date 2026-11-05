"""Pruebas unitarias de la validación de JWT (generan su propio par de llaves; no requieren Keycloak)."""
import importlib
import time
import types

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

ISSUER = "http://localhost:8081/realms/gestion"


@pytest.fixture
def auth(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("JWKS_URL", "http://keycloak:8080/jwks")
    monkeypatch.setenv("OIDC_ISSUER", ISSUER)
    import common.auth as mod
    mod = importlib.reload(mod)
    llave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    mod._jwks = types.SimpleNamespace(get_signing_key_from_jwt=lambda t: types.SimpleNamespace(key=llave.public_key()))
    yield mod, llave
    monkeypatch.delenv("AUTH_ENABLED"); importlib.reload(mod)


def token(llave, **claims):
    base = {"iss": ISSUER, "sub": "u1", "preferred_username": "demo", "exp": int(time.time()) + 300}
    return jwt.encode({**base, **claims}, llave, algorithm="RS256")


def cred(t):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=t)


def test_token_valido_devuelve_el_usuario(auth):
    mod, llave = auth
    assert mod.get_user(cred(token(llave))) == "demo"


def test_sin_token_401(auth):
    mod, _ = auth
    with pytest.raises(HTTPException) as e:
        mod.get_user(None)
    assert e.value.status_code == 401


def test_token_vencido_401(auth):
    mod, llave = auth
    with pytest.raises(HTTPException) as e:
        mod.get_user(cred(token(llave, exp=int(time.time()) - 10)))
    assert e.value.status_code == 401


def test_emisor_incorrecto_401(auth):
    mod, llave = auth
    with pytest.raises(HTTPException) as e:
        mod.get_user(cred(token(llave, iss="http://otro/realms/x")))
    assert e.value.status_code == 401


def test_firma_de_otra_llave_401(auth):
    mod, _ = auth
    otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(HTTPException) as e:
        mod.get_user(cred(token(otra)))
    assert e.value.status_code == 401


def test_sin_autenticacion_asume_usuario_de_desarrollo(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "false")
    import common.auth as mod
    mod = importlib.reload(mod)
    assert mod.get_user(None) == "dev-user"
