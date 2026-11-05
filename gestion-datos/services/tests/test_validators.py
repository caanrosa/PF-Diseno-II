"""Pruebas unitarias de las reglas de validación (no requieren contenedores)."""
import pytest
from fastapi import HTTPException

from common.validators import parse_fecha, validar_persona

BASE = dict(tipo_documento="C.C", nro_documento="1234567890", primer_nombre="Pedro", segundo_nombre="",
            apellidos="Pérez Gómez", fecha_nacimiento="05-mar-2001", genero="Masculino",
            correo="pedro@correo.com", celular="3001234567")


def rechaza(**cambios):
    with pytest.raises(HTTPException) as e:
        validar_persona({**BASE, **cambios})
    assert e.value.status_code == 422
    return " ".join(e.value.detail)


def test_persona_valida_y_segundo_nombre_opcional():
    p = validar_persona(BASE)
    assert p["segundo_nombre"] is None and str(p["fecha_nacimiento"]) == "2001-03-05"


@pytest.mark.parametrize("doc", ["12345678901", "12a45", "", "１２３"])
def test_documento_invalido(doc):
    assert "nro_documento" in rechaza(nro_documento=doc)


def test_documento_de_10_digitos_es_valido():
    assert validar_persona({**BASE, "nro_documento": "1" * 10})["nro_documento"] == "1" * 10


@pytest.mark.parametrize("campo,valor", [("primer_nombre", "Pedro2"), ("primer_nombre", "a" * 31),
                                         ("segundo_nombre", "Juan9"), ("segundo_nombre", "b" * 31),
                                         ("apellidos", "Pérez3"), ("apellidos", "c" * 61)])
def test_nombres_invalidos(campo, valor):
    assert campo in rechaza(**{campo: valor})


def test_limites_exactos_de_nombres():
    assert validar_persona({**BASE, "primer_nombre": "a" * 30, "apellidos": "b" * 60})


def test_nombres_con_tildes_y_enie():
    assert validar_persona({**BASE, "primer_nombre": "Ángela", "apellidos": "Muñoz Núñez"})


@pytest.mark.parametrize("tipo", ["XX", "CC", "t.i", "Cédula"])
def test_tipo_documento_invalido(tipo):
    assert "tipo_documento" in rechaza(tipo_documento=tipo)


@pytest.mark.parametrize("g", ["Otro", "masculino", "F"])
def test_genero_invalido(g):
    assert "genero" in rechaza(genero=g)


@pytest.mark.parametrize("g", ["Masculino", "Femenino", "No binario", "Prefiero no reportar"])
def test_generos_validos(g):
    assert validar_persona({**BASE, "genero": g})["genero"] == g


@pytest.mark.parametrize("mail", ["pedro@", "pedro.com", "@x.com", "a b@x.com"])
def test_correo_invalido(mail):
    assert "correo" in rechaza(correo=mail)


@pytest.mark.parametrize("cel", ["300123456", "30012345678", "300123456a", ""])
def test_celular_invalido(cel):
    assert "celular" in rechaza(celular=cel)


@pytest.mark.parametrize("txt,esperado", [("05-mar-2001", "2001-03-05"), ("5-MAR-2001", "2001-03-05"),
                                          ("2001-03-05", "2001-03-05"), ("31-dic-1999", "1999-12-31")])
def test_formatos_de_fecha_aceptados(txt, esperado):
    assert str(parse_fecha(txt)) == esperado


@pytest.mark.parametrize("txt", ["31-feb-2001", "05/03/2001", "hoy", "05-xyz-2001"])
def test_formatos_de_fecha_rechazados(txt):
    assert parse_fecha(txt) is None


def test_fecha_futura_rechazada():
    assert "futura" in rechaza(fecha_nacimiento="2999-01-01")


def test_campos_obligatorios_faltantes():
    with pytest.raises(HTTPException) as e:
        validar_persona({})
    assert len(e.value.detail) == 8


def test_modificacion_parcial_solo_valida_lo_enviado():
    assert validar_persona({"celular": "3111111111"}, parcial=True) == {"celular": "3111111111"}
    with pytest.raises(HTTPException):
        validar_persona({"celular": "123"}, parcial=True)


def test_modificacion_puede_borrar_segundo_nombre():
    assert validar_persona({"segundo_nombre": ""}, parcial=True) == {"segundo_nombre": None}
