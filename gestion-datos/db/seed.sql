-- Datos ficticios de ejemplo. Se cargan solo la primera vez que se crea el volumen de la BD.
INSERT INTO personas (tipo_documento, nro_documento, primer_nombre, segundo_nombre, apellidos, fecha_nacimiento, genero, correo, celular) VALUES
 ('C.C','1001','Pedro',   NULL,     'Pérez Gómez',     '2008-03-05','Masculino',            'pedro.perez@example.com',   '3001234567'),
 ('C.C','1002','María',   'Camila', 'Rodríguez Silva', '1994-07-21','Femenino',             'maria.rodriguez@example.com','3012345678'),
 ('C.C','1003','Juan',    'Carlos', 'Martínez Rojas',  '1988-11-02','Masculino',            'juan.martinez@example.com', '3023456789'),
 ('C.C','1004','Laura',   NULL,     'Herrera Díaz',    '1999-01-15','Femenino',             'laura.herrera@example.com', '3034567890'),
 ('C.C','1005','Andrés',  'Felipe', 'Gómez Castro',    '1976-09-30','Masculino',            'andres.gomez@example.com',  '3045678901'),
 ('C.C','1006','Sofía',   NULL,     'Vargas Mejía',    '2001-05-12','No binario',           'sofia.vargas@example.com',  '3056789012'),
 ('C.C','1007','Camilo',  NULL,     'Torres Pardo',    '1991-12-08','Prefiero no reportar', 'camilo.torres@example.com', '3067890123'),
 ('C.C','1008','Valentina',NULL,    'Ortiz Ramírez',   '2007-08-19','Femenino',             'valentina.ortiz@example.com','3078901234'),
 ('C.C','1009','Diego',   'Alejandro','Pérez Salazar', '1983-04-25','Masculino',            'diego.perez@example.com',   '3089012345'),
 ('C.C','1010','Natalia', NULL,     'Cruz Beltrán',    '1996-10-03','Femenino',             'natalia.cruz@example.com',  '3090123456');

INSERT INTO logs (tipo_transaccion, documento, usuario, detalle)
SELECT 'CREAR', nro_documento, 'seed', 'Dato de ejemplo' FROM personas;
