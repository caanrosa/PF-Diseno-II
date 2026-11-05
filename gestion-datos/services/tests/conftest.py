"""Configuración común de las pruebas.

Variables de entorno:
  BASE_URL       URL del frontend/proxy (por defecto http://localhost:8080)
  AUTH_ENABLED   "true" si el sistema corre con SSO; las pruebas piden un token a Keycloak
  KC_TOKEN_URL   endpoint de token de Keycloak (por defecto el del realm "gestion" en localhost:8081)
"""
import os
import random
import sys
from pathlib import Path

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))            # permite "from common ..." sin instalar nada

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
AUTH = os.getenv("AUTH_ENABLED", "false").lower() == "true"
KC_TOKEN_URL = os.getenv("KC_TOKEN_URL", "http://localhost:8081/realms/gestion/protocol/openid-connect/token")

PERSONA = {
    "tipo_documento": "C.C", "primer_nombre": "Pedro", "segundo_nombre": "",
    "apellidos": "Pérez Gómez", "fecha_nacimiento": "2001-03-05", "genero": "Masculino",
    "correo": "pedro.prueba@example.com", "celular": "3001234567",
}


def url(servicio: str, ruta: str = "") -> str:
    return f"{BASE_URL}/api/{servicio}/{ruta.lstrip('/')}"


@pytest.fixture(scope="session")
def sistema_activo():
    try:
        requests.get(BASE_URL + "/config.json", timeout=3)
    except requests.RequestException:
        pytest.skip(f"El sistema no responde en {BASE_URL}. Levante los contenedores primero.")


@pytest.fixture(scope="session")
def headers(sistema_activo):
    if not AUTH:
        return {}
    r = requests.post(KC_TOKEN_URL, data={"grant_type": "password", "client_id": "gestion-tests",
                                           "username": "demo", "password": "demo123"}, timeout=10)
    assert r.status_code == 200, f"No se pudo obtener el token de Keycloak: {r.text}"
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def documento(headers):
    """Documento único por prueba; se borra al terminar."""
    doc = str(random.randint(10**8, 10**9 - 1))
    yield doc
    requests.delete(url("borrar", f"personas/{doc}"), headers=headers, timeout=10)


@pytest.fixture
def crear(headers, documento):
    def _crear(**cambios):
        datos = {**PERSONA, "nro_documento": documento, **cambios}
        return requests.post(url("crear", "personas"), data=datos, headers=headers, timeout=10)
    return _crear
