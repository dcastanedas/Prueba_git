from db import conectar_bd

# ---------------------------------------------
# REGISTRO BÁSICO DE EMPLEADO
# ---------------------------------------------
def agregar_empleado(nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO empleados (
            nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo))
    conn.commit()
    conn.close()

# ---------------------------------------------
# CRUD EMPLEADOS
# ---------------------------------------------
def obtener_empleados():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleados")
    empleados = cursor.fetchall()
    conn.close()
    return empleados

def obtener_empleado(id):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empleados WHERE id = %s", (id,))
    empleado = cursor.fetchone()
    conn.close()
    return empleado

def editar_empleado(id, nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE empleados
        SET nombre = %s, cargo = %s, sueldo_ordinario = %s,
            fecha_ingreso = %s, parqueo = %s
        WHERE id = %s
    """, (nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo, id))
    conn.commit()
    conn.close()

def eliminar_empleado(id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empleados WHERE id = %s", (id,))
    conn.commit()
    conn.close()

# ---------------------------------------------
# OBTENER NOMINAS DESDE BD
# ---------------------------------------------
def obtener_nominas(tipo=None):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    if tipo:
        cursor.execute("""
            SELECT n.*, e.nombre AS empleado_nombre
            FROM nominas n
            JOIN empleados e ON n.empleado_id = e.id
            WHERE n.tipo = %s
            ORDER BY n.fecha_generacion DESC
        """, (tipo,))
    else:
        cursor.execute("""
            SELECT n.*, e.nombre AS empleado_nombre
            FROM nominas n
            JOIN empleados e ON n.empleado_id = e.id
            ORDER BY n.fecha_generacion DESC
        """)
    nominas = cursor.fetchall()
    conn.close()
    return nominas

# ---------------------------------------------
# CALCULAR NOMINA (INVOCAR PROCEDIMIENTOS)
# ---------------------------------------------
def calcular_nomina(tipo):
    conn = conectar_bd()
    cursor = conn.cursor()
    if tipo == 'semanal':
        cursor.callproc('calcular_nomina_semanal')
    elif tipo == 'quincenal':
        cursor.callproc('calcular_nomina_quincenal')
    elif tipo == 'mensual':
        cursor.callproc('calcular_nomina_mensual')
    conn.commit()
    conn.close()

# ---------------------------------------------
# CÁLCULO ISR GUATEMALA (uso interno)
# ---------------------------------------------
IGSS_PORCENTAJE = 0.0483

def calcular_isr(sueldo_ordinario):
    if sueldo_ordinario <= 6000:
        return 0
    elif sueldo_ordinario <= 7500:
        excedente = sueldo_ordinario - 6000
        return excedente * 0.05
    elif sueldo_ordinario <= 9000:
        excedente = sueldo_ordinario - 7500
        return (1500 * 0.05) + (excedente * 0.10)
    else:
        excedente = sueldo_ordinario - 9000
        return (1500 * 0.05) + (1500 * 0.10) + (excedente * 0.15)

# ---------------------------------------------
# CÁLCULO COMPLETO DE PLANILLA INDIVIDUAL
# ---------------------------------------------
def calcular_planilla_empleado(emp):
    sueldo = float(emp['sueldo_ordinario'])
    igss = sueldo * IGSS_PORCENTAJE
    isr = calcular_isr(sueldo)

    parqueo = float(emp.get('parqueo', 0))
    uniforme = float(emp.get('descuento_uniforme', 0))
    funerario = float(emp.get('seguro_funerario', 0))
    prestamo = float(emp.get('prestamo_bantrab', 0))
    bonif_quincena = float(emp.get('bonificacion_quincena', 0))
    bonif_productividad = float(emp.get('bonificacion_productividad', 0))

    total_descuentos = igss + parqueo + uniforme + funerario + isr + prestamo
    total_ingresos = sueldo + bonif_quincena + bonif_productividad
    total_recibir = total_ingresos - total_descuentos

    return {
        "id": emp['id'],
        "nombre": emp['nombre'],
        "cargo": emp['cargo'],
        "fecha_ingreso": emp['fecha_ingreso'],
        "fecha_baja": emp.get('fecha_baja', ''),
        "dias_laborados": emp.get('dias_laborados', ''),
        "sueldo_ordinario": sueldo,
        "bonificacion_quincena": bonif_quincena,
        "bonificacion_productividad": bonif_productividad,
        "igss": round(igss, 2),
        "parqueo": parqueo,
        "descuento_uniforme": uniforme,
        "seguro_funerario": funerario,
        "isr": round(isr, 2),
        "prestamo_bantrab": prestamo,
        "total_recibir": round(total_recibir, 2)
    }

def generar_liquidacion(empleado_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.callproc('generar_liquidacion', (empleado_id,))
    conn.commit()
    conn.close()

def obtener_liquidaciones():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.*, e.nombre AS empleado_nombre
        FROM liquidaciones l
        JOIN empleados e ON l.empleado_id = e.id
        ORDER BY l.fecha_liquidacion DESC
    """)
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_estadisticas():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM empleados")
    total_empleados = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS activos FROM empleados WHERE estado = 'activo'")
    empleados_activos = cursor.fetchone()['activos']

    cursor.execute("SELECT COUNT(*) AS inactivos FROM empleados WHERE estado = 'inactivo'")
    empleados_inactivos = cursor.fetchone()['inactivos']

    cursor.execute("SELECT COUNT(*) AS total FROM nominas")
    total_nominas = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS semanal FROM nominas WHERE tipo = 'semanal'")
    semanal = cursor.fetchone()['semanal']

    cursor.execute("SELECT COUNT(*) AS quincenal FROM nominas WHERE tipo = 'quincenal'")
    quincenal = cursor.fetchone()['quincenal']

    cursor.execute("SELECT COUNT(*) AS mensual FROM nominas WHERE tipo = 'mensual'")
    mensual = cursor.fetchone()['mensual']

    cursor.execute("SELECT COUNT(*) AS total FROM liquidaciones")
    total_liquidaciones = cursor.fetchone()['total']

    cursor.execute("SELECT ROUND(AVG(sueldo_ordinario), 2) AS promedio FROM empleados")
    promedio_sueldo = cursor.fetchone()['promedio']

    conn.close()
    return {
        'empleados': total_empleados,
        'activos': empleados_activos,
        'inactivos': empleados_inactivos,
        'nominas': total_nominas,
        'nominas_semanal': semanal,
        'nominas_quincenal': quincenal,
        'nominas_mensual': mensual,
        'liquidaciones': total_liquidaciones,
        'sueldo_promedio': promedio_sueldo or 0.00
    }
