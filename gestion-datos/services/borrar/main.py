from fastapi import Depends, FastAPI, HTTPException
from common.auth import get_user
from common.db import cursor, registrar_log
from common.validators import validar_documento

app = FastAPI(title="Microservicio Borrar Personas")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.delete("/personas/{documento}")
def borrar(documento: str, usuario: str = Depends(get_user)):
    validar_documento(documento)
    with cursor() as cur:
        cur.execute("DELETE FROM personas WHERE nro_documento=%s", (documento,))
        if cur.rowcount == 0:
            raise HTTPException(404, ["Persona no encontrada"])
        registrar_log(cur, "BORRAR", documento, usuario, "Persona eliminada")
    return {"mensaje": "Persona eliminada", "nro_documento": documento}
