import re
from datetime import date
from fastapi import HTTPException, UploadFile

TIPOS_DOC = {"T.I", "C.C"}  # Tarjeta de identidad / Cédula
GENEROS = {"Masculino", "Femenino", "No binario", "Prefiero no reportar"}
REQUERIDOS = ["tipo_documento", "nro_documento", "primer_nombre", "apellidos",
              "fecha_nacimiento", "genero", "correo", "celular"]

L = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
NOMBRE_RE = re.compile(rf"^[{L}]+(?:[ '\-][{L}]+)*$")   # sin números
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
         "sep": 9, "oct": 10, "nov": 11, "dic": 12,
         "jan": 1, "apr": 4, "aug": 8, "dec": 12}
MAX_FOTO = 2 * 1024 * 1024
TIPOS_FOTO = {"image/png", "image/jpeg", "image/webp"}


def parse_fecha(valor: str):
    """Acepta yyyy-mm-dd (calendario) o dd-mmm-yyyy (texto, ej. 05-mar-2001)."""
    try:
        return date.fromisoformat(valor)
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", valor)
    if m and m.group(2).lower() in MESES:
        try:
            return date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            return None
    return None


def validar_documento(valor: str) -> str:
    if not re.fullmatch(r"[0-9]{1,10}", valor or ""):
        raise HTTPException(422, ["nro_documento: debe ser numérico y de máximo 10 dígitos"])
    return valor


def validar_persona(datos: dict, parcial: bool = False) -> dict:
    """Valida y normaliza. parcial=True (modificar): solo valida los campos enviados."""
    e, out = [], {}
    d = {k: (v.strip() if isinstance(v, str) else v) for k, v in datos.items()}
    if not parcial:
        e += [f"{k}: es obligatorio" for k in REQUERIDOS if not d.get(k)]

    if v := d.get("tipo_documento"):
        if v not in TIPOS_DOC:
            e.append("tipo_documento: debe ser T.I o C.C")
        out["tipo_documento"] = v
    if v := d.get("nro_documento"):
        if not re.fullmatch(r"[0-9]{1,10}", v):
            e.append("nro_documento: debe ser numérico y de máximo 10 dígitos")
        out["nro_documento"] = v
    for campo, maximo in (("primer_nombre", 30), ("apellidos", 60)):
        if v := d.get(campo):
            if len(v) > maximo or not NOMBRE_RE.fullmatch(v):
                e.append(f"{campo}: solo letras y máximo {maximo} caracteres")
            out[campo] = v
    if d.get("segundo_nombre") is not None:             # opcional; "" => NULL
        v = d["segundo_nombre"]
        if v and (len(v) > 30 or not NOMBRE_RE.fullmatch(v)):
            e.append("segundo_nombre: solo letras y máximo 30 caracteres")
        out["segundo_nombre"] = v or None
    if v := d.get("fecha_nacimiento"):
        f = parse_fecha(v)
        if not f:
            e.append("fecha_nacimiento: use el calendario o el formato dd-mmm-yyyy")
        elif f > date.today():
            e.append("fecha_nacimiento: no puede ser futura")
        out["fecha_nacimiento"] = f
    if v := d.get("genero"):
        if v not in GENEROS:
            e.append("genero: valor no permitido")
        out["genero"] = v
    if v := d.get("correo"):
        if len(v) > 254 or not EMAIL_RE.fullmatch(v):
            e.append("correo: formato de correo inválido")
        out["correo"] = v
    if v := d.get("celular"):
        if not re.fullmatch(r"[0-9]{10}", v):
            e.append("celular: debe ser numérico y de exactamente 10 dígitos")
        out["celular"] = v
    if e:
        raise HTTPException(422, e)
    return out


def leer_foto(foto: UploadFile | None):
    """Devuelve (bytes, content_type) o (None, None). Máx. 2 MB."""
    if foto is None or not foto.filename:
        return None, None
    if foto.content_type not in TIPOS_FOTO:
        raise HTTPException(422, ["foto: debe ser PNG, JPG o WEBP"])
    contenido = foto.file.read(MAX_FOTO + 1)
    if len(contenido) > MAX_FOTO:
        raise HTTPException(422, ["foto: el archivo no puede superar 2 MB"])
    return contenido, foto.content_type
