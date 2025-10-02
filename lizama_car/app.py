from flask import Flask, render_template, request, redirect, url_for
from db_nexus import db
from datetime import datetime
from bson.objectid import ObjectId
import bcrypt

app = Flask(__name__)
coleccion = db["Administradores"]

# Mostrar todos los usuarios
@app.route("/usuarios")
def mostrar_usuarios():
    usuarios = list(coleccion.find({}, {"password": 0}))  # ocultamos la contraseña en la tabla
    return render_template("usuarios.html", usuarios=usuarios)

# Agregar usuario
@app.route("/usuarios/add", methods=["POST"])
def agregar_usuario():
    username = request.form["usuario"]
    password = request.form["password"].encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())  # encripta la contraseña
    documento = {
        "username": username,
        "password": hashed.decode("utf-8"),
        "rol": "administrador",
        "fecha_creacion": datetime.utcnow()
    }
    coleccion.insert_one(documento)
    return redirect(url_for("mostrar_usuarios"))

# Eliminar usuario
@app.route("/usuarios/delete/<id>", methods=["GET"])
def eliminar_usuario(id):
    coleccion.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_usuarios"))

if __name__ == "__main__":
    app.run(debug=True)
