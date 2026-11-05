# Gestión de Datos Personales — Diseño de Software II (202630)

Aplicación contenerizada de microservicios con CRUD de personas, registro de transacciones, SSO (Keycloak) y consulta en lenguaje natural con RAG en n8n. El diseño completo está en el documento de diseño entregado.

## Arquitectura

```
Navegador ──▶ frontend (nginx: UI + proxy /api/<servicio>/...)
                 ├─▶ crear   ├─▶ modificar   ├─▶ consultar (perfil "consulta")   ├─▶ borrar   └─▶ logs     (FastAPI)
                 └──────────────────────────┬──────────────────────────────────────────────────────┘
                                            ▼
                              db (PostgreSQL 16 + pgvector)  ◀── n8n (chat + RAG, rol n8n_ro de solo lectura)
Keycloak (SSO, perfil "auth") emite los JWT que validan los microservicios.
```

## Cómo correrlo

```bash
cp .env.example .env
docker compose --profile consulta --profile auth up -d --build
```

| Servicio | URL | Acceso |
|---|---|---|
| Aplicación | http://localhost:8080 | Usuario **demo** / clave **demo123** (Keycloak) |
| n8n (chat RAG) | http://localhost:5678 | Cuenta que usted cree la primera vez; ver `n8n/README.md` |
| Keycloak (admin) | http://localhost:8081 | admin / admin (solo desarrollo) |

- **Sin login (desarrollo):** ponga `AUTH_ENABLED=false` en `.env` y levante sin `--profile auth`.
- **Datos de ejemplo:** `db/seed.sql` carga 10 personas ficticias solo cuando el volumen de la base se crea por primera vez. Para reiniciar la base: `docker compose down -v` (borra los datos locales) y volver a levantar.
- **Habilitar / deshabilitar la consulta:** `docker compose --profile consulta up -d consultar` / `docker compose stop consultar`.
- **Agregar usuarios de prueba:** consola de Keycloak → realm *gestion* → Users.

## Pruebas

```bash
pip install -r services/tests/requirements-test.txt
pytest services/tests/test_validators.py services/tests/test_auth.py   # unitarias, no necesitan contenedores
pytest services/tests                                                  # + integración (sistema arriba, AUTH_ENABLED=false)
AUTH_ENABLED=true pytest services/tests                                # con SSO: pide el token a Keycloak (cliente gestion-tests)
```

Cobertura frente a la estrategia del documento: CP-01 a CP-12, CP-14 y CP-15 están automatizados. CP-13 (apagar `consultar`), CP-16 (pregunta en n8n) y CP-17 (persistencia tras reiniciar) se verifican a mano.

## Estructura

```
docker-compose.yml   .env.example
db/        init.sql (esquema, roles)   seed.sql (datos de ejemplo)
common/    db.py  validators.py  auth.py          módulo compartido
services/  Dockerfile  crear/ modificar/ consultar/ borrar/ logs/  tests/
frontend/  index.html (UI + login PKCE)  nginx.conf.template  Dockerfile
keycloak/  realm-gestion.json (importación automática)
n8n/       credentials.json  workflows/  README.md
```
