"""Pruebas de integración: recorren el sistema completo a través del proxy (frontend).
Requieren los contenedores arriba:  docker compose --profile consulta --profile auth up -d
Los IDs CP-xx corresponden a la estrategia de pruebas del documento de diseño."""
import datetime as dt

import requests

from conftest import AUTH, PERSONA, url

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def logs(headers, **filtros):
    r = requests.get(url("logs", "logs"), params=filtros, headers=headers, timeout=10)
    assert r.status_code == 200
    return r.json()


def test_cp01_crear_persona_valida(crear, documento, headers):
    r = crear()
    assert r.status_code == 201 and r.json()["nro_documento"] == documento
    p = requests.get(url("consultar", f"personas/{documento}"), headers=headers, timeout=10).json()
    assert p["primer_nombre"] == "Pedro" and p["segundo_nombre"] is None
    assert any(x["tipo_transaccion"] == "CREAR" for x in logs(headers, documento=documento))


def test_cp02_documento_duplicado(crear):
    assert crear().status_code == 201
    r = crear()
    assert r.status_code == 409 and "ya existe" in " ".join(r.json()["detail"])


def test_cp03_documento_invalido(crear):
    assert crear(nro_documento="12345678901").status_code == 422
    assert crear(nro_documento="12ab").status_code == 422


def test_cp04_nombre_con_numeros(crear):
    r = crear(primer_nombre="Pedro2")
    assert r.status_code == 422 and "primer_nombre" in " ".join(r.json()["detail"])


def test_cp05_celular_invalido(crear):
    assert crear(celular="300123456").status_code == 422


def test_cp06_correo_invalido(crear):
    assert crear(correo="pedro@").status_code == 422


def test_cp07_foto_mayor_a_2mb(headers, documento):
    grande = b"0" * (2 * 1024 * 1024 + 1)
    r = requests.post(url("crear", "personas"), data={**PERSONA, "nro_documento": documento}, headers=headers,
                      files={"foto": ("grande.png", grande, "image/png")}, timeout=20)
    assert r.status_code == 422 and "2 MB" in " ".join(r.json()["detail"])


def test_cp07b_foto_valida_se_guarda_y_se_descarga(headers, documento):
    r = requests.post(url("crear", "personas"), data={**PERSONA, "nro_documento": documento}, headers=headers,
                      files={"foto": ("f.png", PNG, "image/png")}, timeout=10)
    assert r.status_code == 201
    f = requests.get(url("consultar", f"personas/{documento}/foto"), headers=headers, timeout=10)
    assert f.status_code == 200 and f.content == PNG and f.headers["content-type"] == "image/png"


def test_cp08_fecha_escrita_en_texto(crear, documento, headers):
    assert crear(fecha_nacimiento="05-mar-2001").status_code == 201
    p = requests.get(url("consultar", f"personas/{documento}"), headers=headers, timeout=10).json()
    assert p["fecha_nacimiento"] == "2001-03-05"


def test_cp09_modificar_persona(crear, documento, headers):
    crear()
    r = requests.put(url("modificar", f"personas/{documento}"), data={"celular": "3119998877"}, headers=headers, timeout=10)
    assert r.status_code == 200
    p = requests.get(url("consultar", f"personas/{documento}"), headers=headers, timeout=10).json()
    assert p["celular"] == "3119998877" and p["primer_nombre"] == "Pedro"
    assert any(x["tipo_transaccion"] == "MODIFICAR" for x in logs(headers, documento=documento))
    mal = requests.put(url("modificar", f"personas/{documento}"), data={"celular": "12"}, headers=headers, timeout=10)
    assert mal.status_code == 422
    assert requests.put(url("modificar", "personas/999999999"), data={"celular": "3000000000"},
                        headers=headers, timeout=10).status_code == 404


def test_cp10_consultar_existente_inexistente_y_listado(crear, documento, headers):
    crear()
    assert requests.get(url("consultar", f"personas/{documento}"), headers=headers, timeout=10).status_code == 200
    assert requests.get(url("consultar", "personas/999999998"), headers=headers, timeout=10).status_code == 404
    lista = requests.get(url("consultar", "personas"), headers=headers, timeout=10)
    assert lista.status_code == 200 and any(p["nro_documento"] == documento for p in lista.json())
    assert any(x["tipo_transaccion"] == "CONSULTAR" for x in logs(headers, documento=documento))


def test_cp11_borrar_y_conservar_historial(crear, documento, headers):
    crear()
    assert requests.delete(url("borrar", f"personas/{documento}"), headers=headers, timeout=10).status_code == 200
    assert requests.get(url("consultar", f"personas/{documento}"), headers=headers, timeout=10).status_code == 404
    assert requests.delete(url("borrar", f"personas/{documento}"), headers=headers, timeout=10).status_code == 404
    tipos = {x["tipo_transaccion"] for x in logs(headers, documento=documento)}
    assert {"CREAR", "BORRAR"} <= tipos          # el log se conserva aunque la persona ya no exista


def test_cp12_filtros_del_log(crear, documento, headers):
    crear()
    requests.put(url("modificar", f"personas/{documento}"), data={"celular": "3000000001"}, headers=headers, timeout=10)
    solo_crear = logs(headers, documento=documento, tipo="CREAR")
    assert solo_crear and all(x["tipo_transaccion"] == "CREAR" and x["documento"] == documento for x in solo_crear)
    ayer, manana = dt.date.today() - dt.timedelta(days=1), dt.date.today() + dt.timedelta(days=1)
    en_rango = logs(headers, documento=documento, desde=ayer.isoformat(), hasta=manana.isoformat())
    assert {x["tipo_transaccion"] for x in en_rango} >= {"CREAR", "MODIFICAR"}
    assert logs(headers, documento=documento, hasta="2000-01-01") == []
    fechas = [x["fecha"] for x in en_rango]
    assert fechas == sorted(fechas, reverse=True)           # de la más reciente a la más antigua
    assert requests.get(url("logs", "logs"), params={"tipo": "OTRO"}, headers=headers, timeout=10).status_code == 422


def test_cp14_sin_token_401():
    if not AUTH:
        import pytest; pytest.skip("Solo aplica con AUTH_ENABLED=true")
    assert requests.get(url("consultar", "personas"), timeout=10).status_code == 401
    assert requests.get(url("logs", "logs"), timeout=10).status_code == 401


def test_cp15_token_valido_queda_en_el_log(crear, documento, headers):
    if not AUTH:
        import pytest; pytest.skip("Solo aplica con AUTH_ENABLED=true")
    crear()
    assert logs(headers, documento=documento, tipo="CREAR")[0]["usuario"] == "demo"
