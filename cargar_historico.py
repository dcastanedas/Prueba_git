import mysql.connector
from datetime import datetime, timedelta

def conectar_bd():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='gestion_rrhh'
    )

def generar_planillas_historicas():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Obtener todos los empleados con su fecha de ingreso y sueldo
    cursor.execute("SELECT id, sueldo_ordinario, fecha_ingreso FROM empleados")
    empleados = cursor.fetchall()

    fecha_actual = datetime.today()

    for emp in empleados:
        ingreso = emp['fecha_ingreso']
        sueldo = emp['sueldo_ordinario']
        empleado_id = emp['id']

        # Comenzar desde el mes de ingreso
        fecha = ingreso.replace(day=1)

        while fecha < fecha_actual:
            isr = sueldo * 0.05 if sueldo > 48000 else 0
            igss = sueldo * 0.0483
            bonificacion = 250
            total = sueldo - isr - igss + bonificacion

            cursor.execute("""
                INSERT INTO nominas (
                    empleado_id, tipo, periodo_inicio, periodo_fin,
                    salario_bruto, isr, igss, bonificacion, total_neto
                )
                VALUES (%s, 'mensual', %s, %s, %s, %s, %s, %s, %s)
            """, (
                empleado_id,
                fecha.strftime('%Y-%m-01'),
                (fecha + timedelta(days=29)).strftime('%Y-%m-%d'),
                sueldo,
                isr,
                igss,
                bonificacion,
                total
            ))

            # Pasar al siguiente mes
            fecha = (fecha + timedelta(days=32)).replace(day=1)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Planillas históricas generadas exitosamente.")

if __name__ == "__main__":
    generar_planillas_historicas()

