DROP DATABASE IF EXISTS gestion_rrhh;
CREATE DATABASE gestion_rrhh;
USE gestion_rrhh;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'rh') DEFAULT 'rh'
);

-- Usuario admin inicial (contraseña: admin123 en SHA256)
INSERT INTO usuarios (nombre, correo, contrasena, rol)
VALUES ('Admin', 'admin@empresa.com', SHA2('admin123', 256), 'admin');

-- =========================
-- 2. TABLA: EMPLEADOS
-- =========================
CREATE TABLE IF NOT EXISTS empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cargo VARCHAR(100),
    sueldo_ordinario DECIMAL(10,2) NOT NULL,
    fecha_ingreso DATE,
    parqueo DECIMAL(10,2) DEFAULT 0.00,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo'
);

-- =========================
-- 3. TABLA: NOMINAS
-- =========================
CREATE TABLE IF NOT EXISTS nominas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT,
    tipo ENUM('semanal', 'quincenal', 'mensual'),
    periodo_inicio DATE,
    periodo_fin DATE,
    salario_bruto DECIMAL(10,2),
    isr DECIMAL(10,2),
    igss DECIMAL(10,2),
    bonificacion DECIMAL(10,2),
    total_neto DECIMAL(10,2),
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);

-- =========================
-- 4. PROCEDIMIENTOS NOMINA
-- =========================

DELIMITER $$

-- SEMANAL
CREATE PROCEDURE calcular_nomina_semanal()
BEGIN
    DECLARE fin_periodo DATE;
    SET fin_periodo = CURDATE();

    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        e.id,
        'semanal',
        DATE_SUB(fin_periodo, INTERVAL 6 DAY),
        fin_periodo,
        (e.sueldo_ordinario / 4),
        CASE
            WHEN e.sueldo_ordinario > 60000 THEN (e.sueldo_ordinario / 4) * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN (e.sueldo_ordinario / 4) * 0.05
            ELSE 0
        END,
        (e.sueldo_ordinario / 4) * 0.0483,
        62.5,
        (e.sueldo_ordinario / 4)
        - CASE
            WHEN e.sueldo_ordinario > 60000 THEN (e.sueldo_ordinario / 4) * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN (e.sueldo_ordinario / 4) * 0.05
            ELSE 0
        END
        - ((e.sueldo_ordinario / 4) * 0.0483)
        + 62.5
    FROM empleados e
    WHERE e.estado = 'activo';
END$$

-- QUINCENAL
CREATE PROCEDURE calcular_nomina_quincenal()
BEGIN
    DECLARE fin_periodo DATE;
    SET fin_periodo = CURDATE();

    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        e.id,
        'quincenal',
        DATE_SUB(fin_periodo, INTERVAL 14 DAY),
        fin_periodo,
        (e.sueldo_ordinario / 2),
        CASE
            WHEN e.sueldo_ordinario > 60000 THEN (e.sueldo_ordinario / 2) * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN (e.sueldo_ordinario / 2) * 0.05
            ELSE 0
        END,
        (e.sueldo_ordinario / 2) * 0.0483,
        125,
        (e.sueldo_ordinario / 2)
        - CASE
            WHEN e.sueldo_ordinario > 60000 THEN (e.sueldo_ordinario / 2) * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN (e.sueldo_ordinario / 2) * 0.05
            ELSE 0
        END
        - ((e.sueldo_ordinario / 2) * 0.0483)
        + 125
    FROM empleados e
    WHERE e.estado = 'activo';
END$$

-- MENSUAL
CREATE PROCEDURE calcular_nomina_mensual()
BEGIN
    DECLARE fin_periodo DATE;
    SET fin_periodo = CURDATE();

    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        e.id,
        'mensual',
        DATE_SUB(fin_periodo, INTERVAL 30 DAY),
        fin_periodo,
        e.sueldo_ordinario,
        CASE
            WHEN e.sueldo_ordinario > 60000 THEN e.sueldo_ordinario * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN e.sueldo_ordinario * 0.05
            ELSE 0
        END,
        e.sueldo_ordinario * 0.0483,
        250,
        e.sueldo_ordinario
        - CASE
            WHEN e.sueldo_ordinario > 60000 THEN e.sueldo_ordinario * 0.07
            WHEN e.sueldo_ordinario > 48000 THEN e.sueldo_ordinario * 0.05
            ELSE 0
        END
        - (e.sueldo_ordinario * 0.0483)
        + 250
    FROM empleados e
    WHERE e.estado = 'activo';
END$$

DELIMITER ;




CREATE TABLE IF NOT EXISTS liquidaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT,
    fecha_liquidacion DATE,
    anios_trabajados INT,
    dias_vacaciones_pendientes INT,
    bonificacion DECIMAL(10,2),
    vacaciones DECIMAL(10,2),
    indemnizacion DECIMAL(10,2),
    igss DECIMAL(10,2),
    isr DECIMAL(10,2),
    total DECIMAL(10,2),
    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);





DELIMITER $$

CREATE PROCEDURE generar_liquidacion(IN emp_id INT)
BEGIN
    DECLARE fecha_actual DATE;
    DECLARE ingreso DATE;
    DECLARE sueldo DECIMAL(10,2);
    DECLARE anios INT;
    DECLARE vacaciones_dias INT;
    DECLARE bonif DECIMAL(10,2);
    DECLARE vacaciones_pago DECIMAL(10,2);
    DECLARE indemnizacion DECIMAL(10,2);
    DECLARE isr_val DECIMAL(10,2);
    DECLARE igss_val DECIMAL(10,2);
    DECLARE total_liquidar DECIMAL(10,2);

    SET fecha_actual = CURDATE();

    SELECT fecha_ingreso, sueldo_ordinario INTO ingreso, sueldo
    FROM empleados WHERE id = emp_id;

    SET anios = TIMESTAMPDIFF(YEAR, ingreso, fecha_actual);
    SET vacaciones_dias = anios * 15;
    SET bonif = 250; -- asumiendo liquidación en último mes
    SET vacaciones_pago = (sueldo / 30) * vacaciones_dias;
    SET indemnizacion = sueldo * anios;
    SET igss_val = (vacaciones_pago + indemnizacion + bonif) * 0.0483;

    -- ISR simplificado para liquidación
    IF (sueldo * anios) > 60000 THEN
        SET isr_val = (sueldo * anios) * 0.07;
    ELSEIF (sueldo * anios) > 48000 THEN
        SET isr_val = (sueldo * anios) * 0.05;
    ELSE
        SET isr_val = 0;
    END IF;

    SET total_liquidar = vacaciones_pago + indemnizacion + bonif - isr_val - igss_val;

    -- Insertar en tabla
    INSERT INTO liquidaciones (
        empleado_id, fecha_liquidacion, anios_trabajados,
        dias_vacaciones_pendientes, bonificacion, vacaciones,
        indemnizacion, igss, isr, total
    )
    VALUES (
        emp_id, fecha_actual, anios, vacaciones_dias, bonif,
        vacaciones_pago, indemnizacion, igss_val, isr_val, total_liquidar
    );

    -- Marcar empleado como inactivo
    UPDATE empleados SET estado = 'inactivo' WHERE id = emp_id;
END$$

DELIMITER ;

INSERT INTO empleados (nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo, estado)
VALUES 
('Carlos Méndez', 'Contador', 7000.00, '2016-05-12', 150.00, 'activo'),
('Luisa Torres', 'Analista', 5500.00, '2015-03-08', 0.00, 'activo'),
('Jorge Pérez', 'Supervisor', 8200.00, '2017-08-25', 100.00, 'activo'),
('Ana Ramírez', 'Asistente', 3900.00, '2014-10-11', 0.00, 'activo'),
('Marcos Gómez', 'Gerente', 12000.00, '2013-01-20', 200.00, 'activo'),
('Carmen Díaz', 'RRHH', 6000.00, '2012-07-05', 0.00, 'activo'),
('Elena Rodríguez', 'Técnico', 4500.00, '2011-11-03', 50.00, 'activo'),
('Pedro Salazar', 'Diseñador', 5100.00, '2010-02-17', 0.00, 'activo');


USE gestion_rrhh;

SHOW TABLES;

SELECT * FROM usuarios;

SELECT id, nombre, correo, rol FROM usuarios;



CALL calcular_nomina_semanal();
CALL calcular_nomina_quincenal();
CALL calcular_nomina_mensual();
