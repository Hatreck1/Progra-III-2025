from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_nexus import db
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import bcrypt
from flask import make_response

# =============== DECORADOR LOGIN ===============
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        response = make_response(f(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return decorated_function


app = Flask(__name__)
app.secret_key = "tu_clave_secreta_aqui"
# --- Colecciónes de la base de datos las tablas  ---
coleccion_admin = db["Administradores"]
coleccion_vehiculos = db["Vehiculos"]
coleccion_ventas = db["Ventas"]
coleccion_rentas = db["Rentas"]
coleccion_historial = db["Historial_Rentas"]
coleccion_clientes = db["clientes"]


# ==================== LOGIN ====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"].encode("utf-8")
        admin = coleccion_admin.find_one({"username": usuario})
        if admin and bcrypt.checkpw(password, admin["password"].encode("utf-8")):
            session["user"] = admin["username"]
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos",
                hide_navbar=True
            )
    return render_template("login.html", hide_navbar=True)


# ==================== REGISTRO ====================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nuevo_usuario = request.form["nuevo_usuario"]
        nueva_password = request.form["nueva_password"].encode("utf-8")

        if coleccion_admin.find_one({"username": nuevo_usuario}):
            return render_template("register.html", error="Usuario ya existe")

        hashed = bcrypt.hashpw(nueva_password, bcrypt.gensalt())
        documento = {
            "username": nuevo_usuario,
            "password": hashed.decode("utf-8"),
            "rol": "administrador",
            "fecha_creacion": datetime.utcnow()
        }
        coleccion_admin.insert_one(documento)
        return redirect(url_for("login"))
    return render_template("register.html", hide_navbar=True)


# ==================== LOGOUT ====================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ==================== DASHBOARD ====================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ==================== USUARIOS ====================
@app.route("/usuarios")
@login_required
def mostrar_usuarios():
    usuarios = list(coleccion_admin.find({}, {"password": 0}))
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/usuarios/add", methods=["POST"])
@login_required
def agregar_usuario():
    username = request.form["usuario"]
    password = request.form["password"].encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    documento = {
        "username": username,
        "password": hashed.decode("utf-8"),
        "rol": "administrador",
        "fecha_creacion": datetime.utcnow()
    }
    coleccion_admin.insert_one(documento)
    return redirect(url_for("mostrar_usuarios"))

@app.route("/usuarios/delete/<id>")
@login_required
def eliminar_usuario(id):
    coleccion_admin.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_usuarios"))

@app.route("/usuarios/edit/<id>", methods=["POST"])
@login_required
def editar_usuario(id):
    nuevo_usuario = request.form["usuario"]
    nueva_password = request.form["password"]
    update_data = {"username": nuevo_usuario}
    if nueva_password:
        hashed = bcrypt.hashpw(nueva_password.encode("utf-8"), bcrypt.gensalt())
        update_data["password"] = hashed.decode("utf-8")
    coleccion_admin.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    return redirect(url_for("mostrar_usuarios"))


# ==================== VEHÍCULOS ====================
@app.route("/vehiculos")
@login_required
def mostrar_vehiculos():
    vehiculos = list(coleccion_vehiculos.find())
    return render_template("vehiculos.html", vehiculos=vehiculos)

@app.route("/vehiculos/add", methods=["POST"])
@login_required
def agregar_vehiculo():
    marca = request.form["marca"]
    modelo = request.form["modelo"]
    anio = int(request.form["anio"])
    color = request.form["color"]
    tipo = request.form["tipo"]
    transmision = request.form["transmision"]
    combustible = request.form["combustible"]
    kilometraje = request.form["kilometraje"]
    precio_compra = float(request.form["precio_compra"])
    precio = float(request.form["precio"])
    imagen = request.files["imagen"]

    ruta_imagen = None
    if imagen and imagen.filename != "":
        ruta_imagen = f"static/{imagen.filename}"
        imagen.save(ruta_imagen)

    documento = {
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "color": color,
        "tipo": tipo,
        "transmision": transmision,
        "combustible": combustible,
        "kilometraje": kilometraje,
        "precio_compra": precio_compra,
        "precio": precio,  # Precio de venta
        "fecha_compra": datetime.utcnow(),
        "registrado_por": session["user"],
        "imagen": ruta_imagen,
        "rentado": False
    }

    coleccion_vehiculos.insert_one(documento)
    flash("🚗 Vehículo añadido correctamente.", "success")
    return redirect(url_for("mostrar_vehiculos"))

@app.route("/vehiculos/delete/<id>")
@login_required
def eliminar_vehiculo(id):
    vehiculo = coleccion_vehiculos.find_one({"_id": ObjectId(id)})
    if vehiculo:
        if vehiculo.get("rentado", False):
            return redirect(url_for("mostrar_vehiculos"))
        coleccion_vehiculos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_vehiculos"))

@app.route("/vehiculos/vender/<id>")
@login_required
def vender_vehiculo(id):
    vehiculo = coleccion_vehiculos.find_one({"_id": ObjectId(id)})
    if vehiculo:
        venta = {
            "marca": vehiculo["marca"],
            "modelo": vehiculo["modelo"],
            "precio": vehiculo["precio"],
            "imagen": vehiculo.get("imagen", ""),
            "vendedor": session["user"],
            "fecha_venta": datetime.utcnow()
        }
        coleccion_ventas.insert_one(venta)
        coleccion_vehiculos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_vehiculos"))

# ==================== VENTAS ====================
@app.route("/ventas")
@login_required
def mostrar_ventas():
    ventas = list(coleccion_ventas.find())
    return render_template("ventas.html", ventas=ventas)

# ==================== RENTAS ====================
@app.route("/renta")
@login_required
def mostrar_renta():
    vehiculos = list(coleccion_vehiculos.find({"rentado": {"$ne": True}}))
    return render_template("renta.html", vehiculos=vehiculos)

@app.route("/renta/add/<id>", methods=["POST"])
@login_required
def rentar_vehiculo(id):
    cliente_nombre = request.form["cliente_nombre"]
    cliente_dui = request.form["cliente_dui"]
    vehiculo = coleccion_vehiculos.find_one({"_id": ObjectId(id)})
    if vehiculo and not vehiculo.get("rentado", False):
        renta = {
            "vehiculo_id": vehiculo["_id"],
            "marca": vehiculo["marca"],
            "modelo": vehiculo["modelo"],
            "anio": vehiculo["anio"],
            "precio": vehiculo["precio"],
            "imagen": vehiculo.get("imagen", ""),
            "cliente_nombre": cliente_nombre,
            "cliente_dui": cliente_dui,
            "fecha_renta": datetime.utcnow() - timedelta(hours=6),
            "rentado_por": session["user"]
        }
        coleccion_rentas.insert_one(renta)
        coleccion_vehiculos.update_one({"_id": vehiculo["_id"]}, {"$set": {"rentado": True}})
        flash("Vehículo rentado exitosamente.", "success")
    return redirect(url_for("mostrar_renta"))


# ==================== CLIENTES ====================
@app.route("/clientes")
@login_required
def mostrar_clientes():
    clientes = list(coleccion_clientes.find().sort("fecha_registro", -1))
    return render_template("clientes.html", clientes=clientes)

# ✅ Registrar nuevo cliente
@app.route("/clientes/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_cliente():
    if request.method == "POST":
        datos_cliente = {
            "nombre": request.form["nombre"],
            "dui": request.form["dui"],
            "telefono": request.form["telefono"],
            "correo": request.form["correo"],
            "direccion": request.form["direccion"],
            "licencia": request.form["licencia"],
            "tipo_licencia": request.form["tipo_licencia"],
            "fecha_nacimiento": request.form["fecha_nacimiento"],
            "genero": request.form["genero"],
            "fecha_registro": datetime.now(),
            "vendedor": session["user"]
        }
        coleccion_clientes.insert_one(datos_cliente)
        flash("✅ Cliente registrado correctamente.", "success")
        return redirect(url_for("mostrar_clientes"))
    
    # Renderizar el formulario vacío
    return render_template("form_cliente.html", cliente=None)

# ✅ Editar cliente existente
@app.route("/clientes/editar/<id>", methods=["GET", "POST"])
@login_required
def editar_cliente(id):
    cliente = coleccion_clientes.find_one({"_id": ObjectId(id)})
    if not cliente:
        flash("❌ Cliente no encontrado.", "danger")
        return redirect(url_for("mostrar_clientes"))

    if request.method == "POST":
        nuevos_datos = {
            "nombre": request.form["nombre"],
            "dui": request.form["dui"],
            "telefono": request.form["telefono"],
            "correo": request.form["correo"],
            "direccion": request.form["direccion"],
            "licencia": request.form["licencia"],
            "tipo_licencia": request.form["tipo_licencia"],
            "fecha_nacimiento": request.form["fecha_nacimiento"],
            "genero": request.form["genero"],
        }
        coleccion_clientes.update_one({"_id": ObjectId(id)}, {"$set": nuevos_datos})
        flash("✏️ Cliente actualizado correctamente.", "info")
        return redirect(url_for("mostrar_clientes"))

    # Renderizar el formulario con los datos del cliente
    return render_template("form_cliente.html", cliente=cliente)

# ✅ Eliminar cliente
@app.route("/clientes/eliminar/<id>", methods=["POST"])
@login_required
def eliminar_cliente(id):
    coleccion_clientes.delete_one({"_id": ObjectId(id)})
    flash("🗑️ Cliente eliminado correctamente.", "warning")
    return redirect(url_for("mostrar_clientes"))


# ==================== COMPRA DE CARROS LOCAL ====================
# ==================== COMPRA LOCAL ====================
@app.route("/compra_local", methods=["GET", "POST"])
@login_required
def compra_local():
    coleccion_historial_compra_local = db["Historial_compra_local"]
    coleccion_vehiculos = db["Vehiculos"]  # 👈 Asegúrate de que el nombre coincida en la BD

    if request.method == "POST":
        # Datos del vehículo
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        anio = int(request.form["anio"])
        color = request.form["color"]
        tipo = request.form["tipo"]
        transmision = request.form["transmision"]
        combustible = request.form["combustible"]
        kilometraje = request.form["kilometraje"]
        precio_compra = float(request.form["precio_compra"])
        precio = float(request.form["precio"])
        vendedor_nombre = request.form["vendedor_nombre"]
        vendedor_dui = request.form["vendedor_dui"]
        imagen = request.files["imagen"]

        # Guardar imagen en carpeta static
        ruta_imagen = None
        if imagen and imagen.filename != "":
            ruta_imagen = f"static/{imagen.filename}"
            imagen.save(ruta_imagen)

        # Documento para la colección Vehiculos (campos exactos que pediste)
        vehiculo = {
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "color": color,
            "tipo": tipo,
            "transmision": transmision,
            "combustible": combustible,
            "kilometraje": kilometraje,
            "precio_compra": precio_compra,
            "precio": precio,
            "fecha_compra": datetime.utcnow(),
            "registrado_por": session["user"],
            "imagen": ruta_imagen,
            "rentado": False
        }

        # Guardar en la colección Vehiculos
        coleccion_vehiculos.insert_one(vehiculo)

        # Guardar también en el historial (agregando los datos del vendedor)
        historial = vehiculo.copy()
        historial["vendedor_nombre"] = vendedor_nombre
        historial["vendedor_dui"] = vendedor_dui
        coleccion_historial_compra_local.insert_one(historial)

        flash("🚗 Vehículo registrado correctamente en la compra local y agregado a la colección Vehiculos.", "success")
        return redirect(url_for("compra_local"))

    # Mostrar historial de compras locales
    historial_compras = list(
        coleccion_historial_compra_local.find().sort("fecha_compra", -1)
    )

    return render_template("compra_local.html", historial=historial_compras)

# ==================== IMPORTACIÓN historial ====================
@app.route("/historial_importacion")
@login_required
def historial_importacion():
    historial = list(db["Importacion_carros"].find().sort("fecha_registro", -1))

    # normalizar fechas
    for item in historial:
        if isinstance(item.get("fecha_llegada"), str):
            try:
                item["fecha_llegada"] = datetime.fromisoformat(item["fecha_llegada"])
            except:
                pass

    return render_template("historial_importacion.html", historial=historial)

@app.route("/importacion_carros", methods=["GET", "POST"])
@login_required
def importacion_carros():
    coleccion_import = db["Importacion_carros"]
    coleccion_vehiculos = db["Vehiculos"]

    if request.method == "POST":

        marca = request.form.get("marca")
        modelo = request.form.get("modelo")
        anio = int(request.form.get("anio") or 0)
        color = request.form.get("color")
        tipo = request.form.get("tipo")
        transmision = request.form.get("transmision")
        combustible = request.form.get("combustible")
        kilometraje = request.form.get("kilometraje")
        precio_compra = float(request.form.get("precio_compra") or 0)
        precio_venta = float(request.form.get("precio_venta") or 0)

        pais_origen = request.form.get("pais_origen")
        puerto_salida = request.form.get("puerto_salida")
        puerto_llegada = request.form.get("puerto_llegada")
        naviera = request.form.get("naviera")
        num_contenedor = request.form.get("num_contenedor")
        num_booking = request.form.get("num_booking")

        def parse_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except:
                return None

        fecha_salida = parse_date(request.form.get("fecha_salida"))
        fecha_llegada = parse_date(request.form.get("fecha_llegada"))
        fecha_retiro_aduana = parse_date(request.form.get("fecha_retiro_aduana"))

        costo_flete = float(request.form.get("costo_flete") or 0)
        costo_aduana = float(request.form.get("costo_aduana") or 0)
        costo_inspeccion = float(request.form.get("costo_inspeccion") or 0)
        impuestos_pagados = float(request.form.get("impuestos_pagados") or 0)
        transportista_local = request.form.get("transportista_local")
        agencia_aduanal = request.form.get("agencia_aduanal")

        vendedor_nombre = request.form.get("vendedor_nombre")
        vendedor_doc = request.form.get("vendedor_doc")

        imagen = request.files.get("imagen")
        ruta_imagen = None
        if imagen and imagen.filename != "":
            ruta_imagen = f"static/{imagen.filename}"
            imagen.save(ruta_imagen)

        vehiculo = {
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "color": color,
            "tipo": tipo,
            "transmision": transmision,
            "combustible": combustible,
            "kilometraje": kilometraje,
            "precio_compra": precio_compra,
            "precio": precio_venta,   

            "imagen": ruta_imagen,
            "fecha_compra": datetime.utcnow(),
            "registrado_por": session.get("user"),
            "importado": True,
            "info_importacion": {
                "pais_origen": pais_origen,
                "puerto_salida": puerto_salida,
                "puerto_llegada": puerto_llegada,
                "naviera": naviera,
                "num_contenedor": num_contenedor,
                "num_booking": num_booking,
                "fecha_salida": fecha_salida,
                "fecha_llegada": fecha_llegada,
                "fecha_retiro_aduana": fecha_retiro_aduana,
                "costo_flete": costo_flete,
                "costo_aduana": costo_aduana,
                "costo_inspeccion": costo_inspeccion,
                "impuestos_pagados": impuestos_pagados,
                "transportista_local": transportista_local,
                "agencia_aduanal": agencia_aduanal,
                "vendedor_nombre": vendedor_nombre,
                "vendedor_doc": vendedor_doc
            }
        }

        vehiculo_res = coleccion_vehiculos.insert_one(vehiculo)

        registro_import = {
            "vehiculo_id": vehiculo_res.inserted_id,
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "color": color,
            "tipo": tipo,
            "transmision": transmision,
            "combustible": combustible,
            "kilometraje": kilometraje,
            "precio_compra": precio_compra,
            "precio_venta": precio_venta,
            "imagen": ruta_imagen,
            "pais_origen": pais_origen,
            "puerto_salida": puerto_salida,
            "puerto_llegada": puerto_llegada,
            "naviera": naviera,
            "num_contenedor": num_contenedor,
            "num_booking": num_booking,
            "fecha_salida": fecha_salida,
            "fecha_llegada": fecha_llegada,
            "fecha_retiro_aduana": fecha_retiro_aduana,
            "costo_flete": costo_flete,
            "costo_aduana": costo_aduana,
            "costo_inspeccion": costo_inspeccion,
            "impuestos_pagados": impuestos_pagados,
            "transportista_local": transportista_local,
            "agencia_aduanal": agencia_aduanal,
            "vendedor_nombre": vendedor_nombre,
            "vendedor_doc": vendedor_doc,
            "registrado_por": session.get("user"),
            "fecha_registro": datetime.utcnow()
        }

        coleccion_import.insert_one(registro_import)

        flash("✔ Importación registrada correctamente.", "success")
        return redirect(url_for("importacion_carros"))

    historial = list(coleccion_import.find().sort("fecha_registro", -1))
    return render_template("importacion_carros.html", historial=historial)


# ==================== RENTADOS ====================
@app.route("/rentados")
@login_required
def mostrar_rentados():
    rentados = list(coleccion_rentas.find())
    vehiculos_disponibles = list(coleccion_vehiculos.find({"rentado": {"$ne": True}}))
    return render_template("rentados.html", rentados=rentados, vehiculos_disponibles=vehiculos_disponibles)


@app.route("/rentados/devolver/<id>")
@login_required
def devolver_carro(id):
    renta = coleccion_rentas.find_one({"_id": ObjectId(id)})
    if renta:
        # Cambiar el estado del vehículo a disponible
        coleccion_vehiculos.update_one(
            {"_id": renta["vehiculo_id"]},
            {"$set": {"rentado": False}}
        )

        # Registrar la renta finalizada en el historial
        historial = {
            "vehiculo_id": renta["vehiculo_id"],
            "marca": renta["marca"],
            "modelo": renta["modelo"],
            "anio": renta["anio"],
            "precio": renta["precio"],
            "imagen": renta.get("imagen", ""),
            "cliente_nombre": renta["cliente_nombre"],
            "cliente_dui": renta["cliente_dui"],
            "fecha_renta": renta["fecha_renta"],
            "fecha_devolucion": datetime.utcnow() - timedelta(hours=6),
            "rentado_por": renta["rentado_por"]
        }
        coleccion_historial.insert_one(historial)

        # Eliminar de la colección Rentas
        coleccion_rentas.delete_one({"_id": ObjectId(id)})

        flash("Vehículo devuelto y registrado en el historial de rentas.", "success")

    return redirect(url_for("mostrar_rentados"))


@app.route("/rentados/editar/<id>", methods=["POST"])
@login_required
def editar_renta(id):
    cliente_nombre = request.form["cliente_nombre"]
    cliente_dui = request.form["cliente_dui"]
    coleccion_rentas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "cliente_nombre": cliente_nombre,
            "cliente_dui": cliente_dui
        }}
    )
    flash("Renta editada correctamente.", "success")
    return redirect(url_for("mostrar_rentados"))


@app.route("/historial")
@login_required
def mostrar_historial():
    historial = list(coleccion_historial.find().sort("fecha_devolucion", -1))

    # Si no hay datos o alguno no tiene fecha, evitar error
    for item in historial:
        if isinstance(item.get("fecha_renta"), str):
            try:
                item["fecha_renta"] = datetime.fromisoformat(item["fecha_renta"])
            except:
                pass
        if isinstance(item.get("fecha_devolucion"), str):
            try:
                item["fecha_devolucion"] = datetime.fromisoformat(item["fecha_devolucion"])
            except:
                pass

    return render_template("historial_rentas.html", historial=historial)


@app.route("/rentados/rentar/<id>", methods=["POST"])
@login_required
def rentar_desde_rentados(id):
    cliente_nombre = request.form["cliente_nombre"]
    cliente_dui = request.form["cliente_dui"]

    vehiculo = coleccion_vehiculos.find_one({"_id": ObjectId(id)})
    if not vehiculo:
        flash("Vehículo no encontrado.", "error")
        return redirect(url_for("mostrar_rentados"))

    if not vehiculo.get("rentado", False):
        # Crear registro en la colección rentas
        renta = {
            "vehiculo_id": vehiculo["_id"],
            "marca": vehiculo["marca"],
            "modelo": vehiculo["modelo"],
            "anio": vehiculo["anio"],
            "precio": vehiculo["precio"],
            "imagen": vehiculo.get("imagen", ""),
            "cliente_nombre": cliente_nombre,
            "cliente_dui": cliente_dui,
            "fecha_renta": datetime.utcnow() - timedelta(hours=6),
            "rentado_por": session["user"]
        }
        coleccion_rentas.insert_one(renta)

        # Marcar el vehículo como rentado
        coleccion_vehiculos.update_one(
            {"_id": vehiculo["_id"]},
            {"$set": {"rentado": True}}
        )

        flash(f"El vehículo {vehiculo['marca']} {vehiculo['modelo']} ha sido rentado exitosamente.", "success")
    else:
        flash("Este vehículo ya está rentado.", "warning")

    return redirect(url_for("mostrar_rentados"))

# ===============================================
# 🧠 Asistente Automotriz con DeepSeek (Python STREAM)
# ===============================================

from flask import request, jsonify, Response
import requests
import json

@app.route("/deepseek", methods=["POST"])
def deepseek_api():

    if request.method == "OPTIONS":
        return ("", 200)

    if request.method != "POST":
        return jsonify({"error": "Método no permitido. Usa POST."}), 405

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."})

    # ========= MODO CHAT =========
    consulta = data.get("consulta", "")
    modo = data.get("modo", "")

    if modo == "autos" and consulta.strip() != "":
        prompt = f"""
Eres un asesor de ventas en Lizama Car para ayudar a clientes con sus consultas para compra de autos en El Salvador.

Consulta del cliente:
{consulta}

Da una respuesta organizada, útil y breve.
"""
    else:
        # ========= FORMULARIO COMPLETO =========
        nombre_cliente  = data.get("nombre", "Cliente")
        vehiculo        = data.get("vehiculo", "No especificado")
        modelo          = data.get("modelo", "")
        anio            = data.get("anio", "")
        kilometraje     = data.get("kilometraje", "")
        fallas          = data.get("fallas", "")
        sonidos         = data.get("sonidos", "")
        luces_tablero   = data.get("luces", "")
        mantenimiento   = data.get("mantenimiento", "")
        ultima_rev      = data.get("ultima_revision", "")
        descripcion     = data.get("descripcion", "")

        prompt = f"""
Eres un experto automotriz completo: mecánico profesional y asesor de ventas de vehículos.
Responde de forma clara, organizada y útil para un cliente en El Salvador.

📌 Datos del cliente:
- Nombre: {nombre_cliente}
- Vehículo: {vehiculo}
- Modelo: {modelo}
- Año: {anio}
- Kilometraje: {kilometraje}
- Última revisión: {ultima_rev}

🔧 Información reportada:
- Fallas: {fallas}
- Sonidos: {sonidos}
- Luces en tablero: {luces_tablero}
- Descripción: {descripcion}

🔍 Solicitud del cliente:
{mantenimiento}

Incluye:
1. Diagnóstico probable (breve y directo)
2. Causas frecuentes
3. Qué revisar primero
4. Reparaciones sugeridas
5. Repuestos recomendados y económicos
6. Riesgos si NO se repara
7. Costo aproximado en dólares
8. Tiempo estimado en taller
9. Recomendaciones de uso o prevención
10. Si aplica, recomendaciones de carros según presupuesto
"""

    # ========= API KEY =========
    api_key = "sk-0506c409f0bf451f9a94aa4459068056"

    payload = {
        "model": "deepseek-chat",
        "temperature": 0.6,
        "max_tokens": 800,
        "stream": True,
        "messages": [
            {
                "role": "system",
                "content": "Eres un mecánico automotriz certificado y asesor profesional de compra de vehículos. Responde corto, claro y directo."
            },
            {"role": "user", "content": prompt}
        ]
    }

    # ========= FUNCIÓN STREAM =========
    def generar():
        try:
            with requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json=payload,
                stream=True,
                timeout=50
            ) as r:

                for linea in r.iter_lines():
                    if not linea:
                        continue

                    data_raw = linea.decode("utf-8")

                    if not data_raw.startswith("data:"):
                        continue

                    try:
                        json_data = json.loads(data_raw.replace("data: ", ""))
                        delta = json_data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except:
                        pass

        except Exception as e:
            yield f"[ERROR STREAM] {str(e)}"

    # ========= RESPUESTA EN STREAM =========
    return Response(generar(), mimetype="text/plain")

# ==================== RUN ====================
if __name__ == "__main__":
    app.run(debug=True)
