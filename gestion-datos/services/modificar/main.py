from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from common.auth import get_user
from common.db import cursor, registrar_log
from common.validators import leer_foto, validar_documento, validar_persona

app = FastAPI(title="Microservicio Modificar Datos Personales")

COLS = ("tipo_documento, nro_documento, primer_nombre, segundo_nombre, apellidos, "
        "fecha_nacimiento, genero, correo, celular, (foto IS NOT NULL) AS tiene_foto")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/personas/{documento}")
def cargar(documento: str):
    """Carga los datos actuales para precargar el formulario (no genera log de consulta)."""
    validar_documento(documento)
    with cursor() as cur:
        cur.execute(f"SELECT {COLS} FROM personas WHERE nro_documento=%s", (documento,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, ["Persona no encontrada"])
    return row


@app.put("/personas/{documento}")
def modificar(
    documento: str,
    tipo_documento: str = Form(None), primer_nombre: str = Form(None),
    segundo_nombre: str = Form(None), apellidos: str = Form(None),
    fecha_nacimiento: str = Form(None), genero: str = Form(None),
    correo: str = Form(None), celular: str = Form(None),
    foto: UploadFile = File(None), usuario: str = Depends(get_user),
):
    validar_documento(documento)  # el documento es la llave: no se modifica
    cambios = validar_persona(dict(
        tipo_documento=tipo_documento, primer_nombre=primer_nombre, segundo_nombre=segundo_nombre,
        apellidos=apellidos, fecha_nacimiento=fecha_nacimiento, genero=genero,
        correo=correo, celular=celular), parcial=True)
    foto_bytes, foto_tipo = leer_foto(foto)
    if foto_bytes:
        cambios.update(foto=foto_bytes, foto_tipo=foto_tipo)
    if not cambios:
        raise HTTPException(422, ["No se envió ningún campo para modificar"])

    # los nombres de columna vienen de validar_persona (lista blanca), no del usuario
    sets = ", ".join(f"{k}=%({k})s" for k in cambios) + ", actualizado_en=now()"
    with cursor() as cur:
        cur.execute(f"UPDATE personas SET {sets} WHERE nro_documento=%(_doc)s",
                    {**cambios, "_doc": documento})
        if cur.rowcount == 0:
            raise HTTPException(404, ["Persona no encontrada"])
        campos = ", ".join(k for k in cambios if k not in ("foto", "foto_tipo")) + (
            ", foto" if foto_bytes else "")
        registrar_log(cur, "MODIFICAR", documento, usuario, f"Campos: {campos}")
    return {"mensaje": "Persona actualizada", "nro_documento": documento}
