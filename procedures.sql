USE gestion_rrhh;

-- ================================
-- PROCEDIMIENTO: generar_liquidacion
-- ================================
DELIMITER $$

DROP PROCEDURE IF EXISTS generar_liquidacion $$
CREATE PROCEDURE generar_liquidacion(IN emp_id INT)
BEGIN
    DECLARE sueldo DECIMAL(10,2);
    DECLARE fecha_ingreso DATE;
    DECLARE dias_trabajados INT DEFAULT 0;
    DECLARE vacaciones DECIMAL(10,2);
    DECLARE total DECIMAL(10,2);

    SELECT sueldo_ordinario, fecha_ingreso INTO sueldo, fecha_ingreso
    FROM empleados WHERE id = emp_id;

    SET dias_trabajados = DATEDIFF(CURDATE(), fecha_ingreso);

    -- Bonificación por vacaciones no tomadas (por cada año no tomado)
    SET vacaciones = FLOOR(dias_trabajados / 365) * (sueldo / 2);

    -- Total de liquidación: sueldo base + vacaciones
    SET total = sueldo + vacaciones;

    INSERT INTO liquidaciones (
        empleado_id, sueldo_base, compensacion_vacaciones, total_liquidacion, fecha_liquidacion
    ) VALUES (
        emp_id, sueldo, vacaciones, total, CURDATE()
    );

    -- Marcar empleado como inactivo
    UPDATE empleados SET estado = 'inactivo' WHERE id = emp_id;
END $$
DELIMITER ;

-- ================================
-- PROCEDIMIENTO: calcular_nomina_semanal
-- ================================
DELIMITER $$

DROP PROCEDURE IF EXISTS calcular_nomina_semanal $$
CREATE PROCEDURE calcular_nomina_semanal()
BEGIN
    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        id,
        'semanal',
        DATE_SUB(CURDATE(), INTERVAL 6 DAY),
        CURDATE(),
        sueldo_ordinario / 4,
        sueldo_ordinario * 0.05,
        sueldo_ordinario * 0.0483,
        250,
        (sueldo_ordinario / 4 - sueldo_ordinario * 0.05 - sueldo_ordinario * 0.0483 + 250)
    FROM empleados
    WHERE estado = 'activo';
END $$
DELIMITER ;

-- ================================
-- PROCEDIMIENTO: calcular_nomina_quincenal
-- ================================
DELIMITER $$

DROP PROCEDURE IF EXISTS calcular_nomina_quincenal $$
CREATE PROCEDURE calcular_nomina_quincenal()
BEGIN
    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        id,
        'quincenal',
        DATE_SUB(CURDATE(), INTERVAL 14 DAY),
        CURDATE(),
        sueldo_ordinario / 2,
        sueldo_ordinario * 0.05,
        sueldo_ordinario * 0.0483,
        250,
        (sueldo_ordinario / 2 - sueldo_ordinario * 0.05 - sueldo_ordinario * 0.0483 + 250)
    FROM empleados
    WHERE estado = 'activo';
END $$
DELIMITER ;

-- ================================
-- PROCEDIMIENTO: calcular_nomina_mensual
-- ================================
DELIMITER $$

DROP PROCEDURE IF EXISTS calcular_nomina_mensual $$
CREATE PROCEDURE calcular_nomina_mensual()
BEGIN
    INSERT INTO nominas (
        empleado_id, tipo, periodo_inicio, periodo_fin,
        salario_bruto, isr, igss, bonificacion, total_neto
    )
    SELECT
        id,
        'mensual',
        DATE_SUB(CURDATE(), INTERVAL 29 DAY),
        CURDATE(),
        sueldo_ordinario,
        sueldo_ordinario * 0.05,
        sueldo_ordinario * 0.0483,
        250,
        (sueldo_ordinario - sueldo_ordinario * 0.05 - sueldo_ordinario * 0.0483 + 250)
    FROM empleados
    WHERE estado = 'activo';
END $$
DELIMITER ;
