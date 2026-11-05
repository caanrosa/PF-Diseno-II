# n8n: chat en lenguaje natural con RAG

Esta carpeta se monta en el contenedor de n8n como `/seed` y, **solo en el primer arranque del volumen**, se importan:

| Archivo | Contenido |
|---|---|
| `credentials.json` | Credencial **Postgres n8n_ro (solo lectura)**: host `db`, base `personas_db`, usuario `n8n_ro`. |
| `workflows/01_ingesta_personas.json` | Flujo A: lee las personas, genera embeddings y los guarda en pgvector (tabla `personas_vectores`). |
| `workflows/02_chat_rag_personas.json` | Flujo B: chat con un agente que usa búsqueda semántica y SQL de solo lectura. |

## Puesta en marcha (una sola vez)

1. Abra <http://localhost:5678> y cree la cuenta de propietario de n8n (queda solo en su equipo).
2. En **Workflows** deben aparecer los dos flujos. Si no aparecen, vea "Importación manual" más abajo.
3. **Clave de OpenAI.** Abra el flujo 01, pulse el nodo *Embeddings OpenAI* → *Credential* → *Create new*, pegue su API key y guarde. En el nodo *Modelo de chat* y en *Embeddings OpenAI (consulta)* del flujo 02 elija esa misma credencial.
4. **Ingesta.** En el flujo 01 pulse **Execute workflow**. Debe terminar en verde y crear la tabla `personas_vectores`. Luego active el flujo (interruptor *Active*) para que se actualice cada 15 minutos.
5. **Chat.** Abra el flujo 02 y pulse **Open chat** (botón inferior). Pregunte, por ejemplo:
   - ¿Cuál es el empleado más joven que se ha registrado? → con los datos de ejemplo responde **Pedro Pérez**.
   - ¿Cuántas personas hay registradas?
   - ¿Quién tiene el apellido Pérez?
   - ¿Cuál es el promedio de edad?

> Las personas nuevas aparecen en la búsqueda semántica después de la siguiente ingesta (o ejecutándola a mano). La herramienta SQL siempre consulta los datos en vivo.

## Cómo funciona

- **Ingesta:** `DROP TABLE IF EXISTS personas_vectores` → `SELECT` de personas (se construye un texto por persona con nombre, documento, fecha de nacimiento y género; **sin correo ni celular**) → embeddings → PGVector. Se reconstruye todo el índice, por eso nunca hay personas duplicadas ni fichas de personas borradas.
- **Chat:** el agente decide qué herramienta usar. `buscar_personas` hace búsqueda semántica en pgvector; `consultar_sql` ejecuta un `SELECT` con el rol `n8n_ro`, que solo puede leer (sin foto) y no puede modificar `personas`. Las preguntas de agregación (más joven, conteos, promedios) las resuelve SQL, porque la similitud vectorial no puede calcularlas.

## Cambiar de proveedor de IA

Los modelos son nodos reemplazables: cambie *Modelo de chat* y los dos nodos de *Embeddings* por los de Google Gemini u Ollama (modelo local, recomendable si se usan datos reales). Si cambia el modelo de embeddings, ejecute de nuevo el flujo 01: reconstruye la tabla con las dimensiones nuevas.

## Importación manual (si el sembrado automático falla)

1. *Credentials → Create credential → Postgres*: host `db`, database `personas_db`, user `n8n_ro`, password `n8n_ro_pass` (cámbiela fuera de desarrollo), SSL `disable`, puerto `5432`.
2. *Workflows → ⋯ → Import from file* con cada JSON de `workflows/`, y elija la credencial en los nodos marcados.

Para repetir el sembrado automático (sobrescribe los flujos importados): `docker compose exec n8n rm /home/node/.n8n/.sembrado` y `docker compose restart n8n`.
