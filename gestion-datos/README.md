# Gestión de Datos Personales 

## Cómo correrlo

```bash
cp .env.example .env
docker compose --profile consulta up -d --build   # imagenes de todo
# UI:  http://localhost:8080      n8n: http://localhost:5678

# el comando docker compose puede fallar, entonces, en caso tal primero ejecuten imagen por imagen
docker pull pgvector/pgvector:pg16
docker pull n8nio/n8n:latest
docker pull python:3.12-slim
docker pull nginx:1.27-alpine

# E indiferentemente de cómo lo hagan, se demorará un montón de tiempo porque descarga las imágenes por primera vez.


docker compose stop consultar                      # deshabilitar la consulta
docker compose --profile consulta up -d consultar  # habilitarla de nuevo
```
Con `consultar` apagado, la UI muestra "El servicio no está disponible" en esa opción y el resto sigue funcionando.

## Pruebas rápidas con curl
```bash
curl -F tipo_documento=C.C -F nro_documento=1001 -F primer_nombre=Pedro -F apellidos=Pérez \
     -F fecha_nacimiento=05-mar-2001 -F genero=Masculino -F correo=p@x.com -F celular=3001234567 \
     http://localhost:8080/api/crear/personas
curl http://localhost:8080/api/consultar/personas/1001
curl "http://localhost:8080/api/logs/logs?tipo=CREAR&documento=1001"
curl -X DELETE http://localhost:8080/api/borrar/personas/1001
```

