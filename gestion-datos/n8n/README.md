# n8n: chat en lenguaje natural con RAG (Google Gemini)

Esta carpeta se monta en el contenedor de n8n como `/seed`. Solo en el **primer arranque del volumen** se importan:

| Archivo | Contenido |
|---|---|
| `credentials.json` | Credencial **Postgres n8n_ro (solo lectura)**: host `db`, base `personas_db`, usuario `n8n_ro`. |
| `workflows/01_ingesta_personas.json` | Flujo A: lee las personas, genera embeddings con Gemini y los guarda en pgvector (tabla `personas_vectores`). |
| `workflows/02_chat_rag_personas.json` | Flujo B: chat con un agente (Gemini) que usa búsqueda semántica y SQL de solo lectura. |

Los flujos usan **Google Gemini**, que tiene capa gratuita. La variante con OpenAI (de pago) está en `alternativas/openai/`.

## 1. Conseguir la API key de Gemini (gratis)

1. Entre a <https://aistudio.google.com/apikey> con una cuenta de Google.
2. Pulse **Create API key** (si pide un proyecto, elija *Create API key in new project*).
3. Copie la clave. No la suba a GitHub ni la comparta.

## 2. Configurarla en n8n (una sola vez)

1. En *Workflows* abra **01 - Ingesta de personas (RAG)** y haga doble clic en el nodo **Embeddings Gemini**.
2. En *Credential to connect with* pulse **Create new credential**, pegue la clave en **API Key** (deje el *Host* por defecto) y **Save**. Debe salir un mensaje verde.
3. Revise el campo **Model**: debe quedar un modelo de embeddings (por defecto `models/gemini-embedding-001`). Si n8n marca error de modelo, abra la lista desplegable y elija uno que contenga `embedding`. Guarde con `Ctrl + S`.
4. Abra **02 - Chat RAG de personas**. En **Modelo de chat** y en **Embeddings Gemini (consulta)** elija la misma credencial. En *Embeddings Gemini (consulta)* el modelo debe ser **exactamente el mismo** que usó en el flujo 01. Guarde.

## 3. Ejecutar

1. **Ingesta.** En el flujo 01 pulse **Execute workflow**. Todos los nodos deben quedar en verde y se crea la tabla `personas_vectores`. Luego active el flujo (*Active*) para que se actualice cada 15 minutos.
2. **Chat.** En el flujo 02 pulse **Open chat** y pregunte:
   - ¿Cuál es el empleado más joven que se ha registrado? → con los datos de ejemplo responde **Pedro Pérez**.
   - ¿Cuántas personas hay registradas?
   - ¿Quién tiene el apellido Pérez?
   - ¿Cuál es el promedio de edad?

> Las personas nuevas entran a la búsqueda semántica en la siguiente ingesta (o al ejecutarla a mano). La herramienta SQL siempre consulta los datos en vivo.

## Limitaciones de la capa gratuita

- **Límite de peticiones por minuto.** Cada pregunta puede usar varias llamadas (el agente consulta herramientas). Si aparece un error 429 o "quota exceeded", espere un minuto y repita.
- **Privacidad.** Con la capa gratuita, Google puede usar lo que se envía para mejorar sus productos. Use solo datos ficticios (como los de `db/seed.sql`). Para datos reales use un modelo local (Ollama) o un plan de pago con garantías de tratamiento de datos.
- **Cambios de modelos.** Google renueva sus modelos con frecuencia. Si un modelo deja de estar disponible, elíjalo de nuevo en la lista del nodo (chat: cualquier `gemini-…-flash`).

## Cómo funciona

- **Ingesta:** `DROP TABLE IF EXISTS personas_vectores` → `SELECT` de personas (un texto por persona con nombre, documento, fecha de nacimiento y género; **sin correo ni celular**) → embeddings → PGVector. Se reconstruye todo el índice, por eso no hay personas duplicadas ni fichas de personas borradas.
- **Chat:** el agente elige la herramienta. `buscar_personas` hace búsqueda semántica en pgvector; `consultar_sql` ejecuta un `SELECT` con el rol `n8n_ro`, que solo puede leer (sin foto). Las preguntas de agregación (más joven, conteos, promedios) las resuelve SQL, porque la similitud vectorial no puede calcularlas.

## Actualizar los flujos en un n8n que ya está corriendo

Si reemplazó esta carpeta `n8n/` en su proyecto, ejecute (desde la carpeta del proyecto):

```powershell
docker compose exec n8n n8n import:workflow --separate --input=/seed/workflows
```

Los flujos se sobrescriben (mismo identificador). Recargue el navegador y repita el paso 2 de arriba para asignar la credencial de Gemini.

## Importación manual (si el sembrado automático falla)

1. *Credentials → Create credential → Postgres*: host `db`, database `personas_db`, user `n8n_ro`, password `n8n_ro_pass` (cámbiela fuera de desarrollo), SSL `disable`, puerto `5432`.
2. *Workflows → ⋯ → Import from file* con cada JSON de `workflows/`, y elija las credenciales en los nodos marcados.

Para repetir el sembrado automático: `docker compose exec n8n rm /home/node/.n8n/.sembrado` y `docker compose restart n8n`.
