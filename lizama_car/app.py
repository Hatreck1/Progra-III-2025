from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_nexus import db
from datetime import datetime
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

coleccion_admin = db["Administradores"]
coleccion_vehiculos = db["Vehiculos"]
coleccion_ventas = db["Ventas"]
coleccion_rentas = db["Rentas"]

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
    anio = request.form["anio"]
    precio = request.form["precio"]
    imagen = request.files["imagen"]
    ruta_imagen = f"static/{imagen.filename}"
    imagen.save(ruta_imagen)

    documento = {
        "marca": marca,
        "modelo": modelo,
        "anio": int(anio),
        "precio": float(precio),
        "imagen": ruta_imagen,
        "rentado": False
    }
    coleccion_vehiculos.insert_one(documento)
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
            "fecha_renta": datetime.utcnow(),
            "rentado_por": session["user"]
        }
        coleccion_rentas.insert_one(renta)
        coleccion_vehiculos.update_one({"_id": vehiculo["_id"]}, {"$set": {"rentado": True}})
        flash("Vehículo rentado exitosamente.", "success")
    return redirect(url_for("mostrar_renta"))

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
        coleccion_vehiculos.update_one({"_id": renta["vehiculo_id"]}, {"$set": {"rentado": False}})
        coleccion_rentas.delete_one({"_id": ObjectId(id)})
        flash("Vehículo devuelto correctamente.", "success")
    return redirect(url_for("mostrar_rentados"))

@app.route("/rentados/editar/<id>", methods=["POST"])
@login_required
def editar_renta(id):
    cliente_nombre = request.form["cliente_nombre"]
    cliente_dui = request.form["cliente_dui"]
    coleccion_rentas.update_one({"_id": ObjectId(id)}, {"$set": {
        "cliente_nombre": cliente_nombre,
        "cliente_dui": cliente_dui
    }})
    flash("Renta editada correctamente.", "success")
    return redirect(url_for("mostrar_rentados"))
@app.route("/rentados/rentar/<id>", methods=["POST"])
def rentar_desde_rentados(id):
    vehiculo = coleccion_vehiculos.find_one({"_id": ObjectId(id)})
    if not vehiculo:
        flash("Vehículo no encontrado.", "error")
        return redirect(url_for("mostrar_rentados"))

    # Marcar como rentado
    coleccion_vehiculos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"rentado": True}}
    )

    flash(f"El vehículo {vehiculo['marca']} {vehiculo['modelo']} ha sido rentado.", "success")
    return redirect(url_for("mostrar_rentados"))


# ==================== RUN ====================
if __name__ == "__main__":
    app.run(debug=True)
