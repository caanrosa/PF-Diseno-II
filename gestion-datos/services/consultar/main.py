from fastapi import Depends, FastAPI, HTTPException, Response
from common.auth import get_user
from common.db import cursor, registrar_log
from common.validators import validar_documento

app = FastAPI(title="Microservicio Consultar Personas")

COLS = ("tipo_documento, nro_documento, primer_nombre, segundo_nombre, apellidos, "
        "fecha_nacimiento, genero, correo, celular, (foto IS NOT NULL) AS tiene_foto")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/personas")
def listar(usuario: str = Depends(get_user)):
    with cursor() as cur:
        cur.execute(f"SELECT {COLS} FROM personas ORDER BY apellidos, primer_nombre LIMIT 500")
        rows = cur.fetchall()
        registrar_log(cur, "CONSULTAR", "*", usuario, f"Listado ({len(rows)} registros)")
    return rows


@app.get("/personas/{documento}")
def consultar(documento: str, usuario: str = Depends(get_user)):
    validar_documento(documento)
    with cursor() as cur:
        cur.execute(f"SELECT {COLS} FROM personas WHERE nro_documento=%s", (documento,))
        row = cur.fetchone()
        registrar_log(cur, "CONSULTAR", documento, usuario, "Encontrada" if row else "No encontrada")
    if not row:
        raise HTTPException(404, ["Persona no encontrada"])
    return row


@app.get("/personas/{documento}/foto")
def foto(documento: str):
    validar_documento(documento)
    with cursor() as cur:
        cur.execute("SELECT foto, foto_tipo FROM personas WHERE nro_documento=%s", (documento,))
        row = cur.fetchone()
    if not row or not row["foto"]:
        raise HTTPException(404, ["Sin foto"])
    return Response(bytes(row["foto"]), media_type=row["foto_tipo"])
