from datetime import date
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from common.auth import get_user
from common.db import cursor
from common.validators import validar_documento

app = FastAPI(title="Microservicio Consulta de Logs")
TIPOS = {"CREAR", "MODIFICAR", "CONSULTAR", "BORRAR"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/logs")
def consultar_logs(tipo: Optional[str] = None, documento: Optional[str] = None,
                   desde: Optional[date] = None, hasta: Optional[date] = None,
                   usuario: str = Depends(get_user)):
    """Filtros combinables: tipo de transacción, documento y rango de fechas (inclusivo)."""
    where, params = [], []
    if tipo:
        if tipo.upper() not in TIPOS:
            raise HTTPException(422, [f"tipo: debe ser uno de {sorted(TIPOS)}"])
        where.append("tipo_transaccion=%s"); params.append(tipo.upper())
    if documento:
        where.append("documento=%s"); params.append(validar_documento(documento))
    if desde:
        where.append("fecha::date >= %s"); params.append(desde)
    if hasta:
        where.append("fecha::date <= %s"); params.append(hasta)
    sql = "SELECT id, tipo_transaccion, documento, usuario, detalle, fecha FROM logs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY fecha DESC LIMIT 500"
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()
