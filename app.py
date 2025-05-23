from flask import Flask, render_template, request, redirect, session, jsonify
from db import conectar_bd
from models import (
    agregar_empleado,
    obtener_empleados,
    obtener_empleado,
    editar_empleado,
    eliminar_empleado,
    calcular_planilla_empleado,
    obtener_nominas,
    generar_liquidacion,
    obtener_liquidaciones,
    obtener_estadisticas,
    calcular_nomina,
)
import hashlib

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2024'
app.config['SESSION_COOKIE_DOMAIN'] = False 
def encriptar_contrasena(contrasena):
    return hashlib.sha256(contrasena.encode()).hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo'].strip()
        contrasena = request.form['contrasena'].strip()

        print(">>> FORMULARIO:")
        print("Correo ingresado:", correo)
        print("Contraseña ingresada (plana):", contrasena)

        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        user = cursor.fetchone()
        conn.close()

        hashed = encriptar_contrasena(contrasena)
        print(">>> HASH generado:", hashed)

        if user:
            print(">>> USUARIO ENCONTRADO:", user)
            print(">>> CONTRASEÑA BD:", user['contrasena'])
        else:
            print(">>> USUARIO NO ENCONTRADO")

        if user and user['contrasena'] == hashed:
            session['user_id'] = user['id']
            session['nombre'] = user['nombre']
            session['rol'] = user['rol']
            print(">>> LOGIN EXITOSO")
            return redirect('/')
        else:
            print(">>> LOGIN FALLIDO: credenciales incorrectas")
            return render_template('login.html', error='Credenciales incorrectas')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    stats = obtener_estadisticas()
    return render_template('dashboard.html', usuario=session, stats=stats)

@app.route('/empleados')
def empleados():
    if 'user_id' not in session:
        return redirect('/login')
    lista = obtener_empleados()
    return render_template('empleados.html', empleados=lista)

@app.route('/empleados/agregar', methods=['GET', 'POST'])
def agregar_empleado_ruta():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        nombre = request.form['nombre']
        cargo = request.form['cargo']
        sueldo_ordinario = request.form['sueldo_ordinario']
        fecha_ingreso = request.form['fecha_ingreso']
        parqueo = request.form['parqueo']

        agregar_empleado(nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo)
        return redirect('/empleados')
    return render_template('agregar_empleado.html')


@app.route('/empleado/editar/<int:id>', methods=['GET', 'POST'])
def editar_empleado_ruta(id):
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        nombre = request.form['nombre']
        cargo = request.form['cargo']
        sueldo_ordinario = request.form['sueldo_ordinario']
        fecha_ingreso = request.form['fecha_ingreso']
        parqueo = request.form['parqueo']

        editar_empleado(id, nombre, cargo, sueldo_ordinario, fecha_ingreso, parqueo)
        return redirect('/empleados')
    
    empleado = obtener_empleado(id)
    return render_template('editar_empleado.html', empleado=empleado)


@app.route('/empleado/eliminar/<int:id>')
def eliminar_empleado_ruta(id):
    eliminar_empleado(id)
    return redirect('/empleados')

@app.route('/ver_planilla')
def ver_planilla():
    tipo = request.args.get('tipo')
    if tipo:
        calcular_nomina(tipo) 
    nominas = obtener_nominas(tipo)
    return render_template('planilla.html', planilla=nominas, tipo=tipo)


@app.route('/generar_liquidacion/<int:empleado_id>')
def generar_liquidacion_ruta(empleado_id):
    generar_liquidacion(empleado_id)
    return redirect('/empleados')

@app.route('/ver_liquidaciones')
def ver_liquidaciones():
    lista = obtener_liquidaciones()
    return render_template('liquidaciones.html', liquidaciones=lista)

@app.route('/estadisticas')
def estadisticas():
    data = obtener_estadisticas()
    return render_template('estadisticas.html', data=data)

# NUEVAS RUTAS PARA USUARIOS (ADMIN)
@app.route('/usuarios')
def ver_usuarios():
    if 'user_id' not in session or session['rol'] != 'admin':
        return redirect('/login')
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, correo, rol FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if 'user_id' not in session or session['rol'] != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        rol = request.form['rol']
        hashed = encriptar_contrasena(contrasena)

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)",
                       (nombre, correo, hashed, rol))
        conn.commit()
        conn.close()
        return redirect('/usuarios')
    return render_template('crear_usuario.html')


if __name__ == '__main__':
    app.run(debug=True)
