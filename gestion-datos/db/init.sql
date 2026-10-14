-- pgvector queda listo para la fase RAG con n8n
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE personas (
    nro_documento    VARCHAR(10) PRIMARY KEY,           -- llave de búsqueda
    tipo_documento   VARCHAR(3)  NOT NULL CHECK (tipo_documento IN ('T.I','C.C')),
    primer_nombre    VARCHAR(30) NOT NULL,
    segundo_nombre   VARCHAR(30),
    apellidos        VARCHAR(60) NOT NULL,
    fecha_nacimiento DATE        NOT NULL,
    genero           VARCHAR(20) NOT NULL
        CHECK (genero IN ('Masculino','Femenino','No binario','Prefiero no reportar')),
    correo           VARCHAR(254) NOT NULL,
    celular          CHAR(10)    NOT NULL,
    foto             BYTEA,
    foto_tipo        VARCHAR(50),
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE logs (
    id                BIGSERIAL PRIMARY KEY,
    tipo_transaccion  VARCHAR(10) NOT NULL CHECK (tipo_transaccion IN ('CREAR','MODIFICAR','CONSULTAR','BORRAR')),
    documento         VARCHAR(10) NOT NULL,   -- '*' cuando es un listado
    usuario           VARCHAR(100) NOT NULL,
    detalle           TEXT,
    fecha             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_logs_doc   ON logs (documento);
CREATE INDEX idx_logs_tipo  ON logs (tipo_transaccion);
CREATE INDEX idx_logs_fecha ON logs (fecha);

-- Usuario de solo lectura para n8n (sin acceso a la foto). CAMBIAR la clave fuera de desarrollo.
CREATE ROLE n8n_ro LOGIN PASSWORD 'n8n_ro_pass';
GRANT CONNECT ON DATABASE personas_db TO n8n_ro;
GRANT USAGE ON SCHEMA public TO n8n_ro;
GRANT SELECT (nro_documento, tipo_documento, primer_nombre, segundo_nombre, apellidos,
              fecha_nacimiento, genero, correo, celular, creado_en) ON personas TO n8n_ro;
-- Para el vector store de n8n (PGVector crea su propia tabla):
GRANT CREATE ON SCHEMA public TO n8n_ro;
