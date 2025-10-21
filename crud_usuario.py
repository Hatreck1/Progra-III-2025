import crud_academico

db = crud_academico.crud()

class crud_usuario:
    def consultar(self, buscar):
        # Busca por nombre o usuario
        sql = "SELECT * FROM usuarios WHERE nombre LIKE %s OR usuario LIKE %s"
        valores = (f"%{buscar}%", f"%{buscar}%")
        return db.consultar(sql, valores)

    def administrar(self, datos):
        if datos['accion'] == "nuevo":
            sql = """
                INSERT INTO usuarios (usuario, clave, nombre, dirección, teléfono)
                VALUES (%s, %s, %s, %s, %s)
            """
            valores = (datos['usuario'], datos['clave'], datos['nombre'], datos['direccion'], datos['telefono'])

        elif datos['accion'] == "modificar":
            sql = """
                UPDATE usuarios SET usuario=%s, clave=%s, nombre=%s, dirección=%s, teléfono=%s
                WHERE idUsuario=%s
            """
            valores = (datos['usuario'], datos['clave'], datos['nombre'], datos['direccion'], datos['telefono'], datos['idUsuario'])

        elif datos['accion'] == "eliminar":
            sql = "DELETE FROM usuarios WHERE idUsuario=%s"
            valores = (datos['idUsuario'],)

        else:
            return {"msg": "Acción no válida"}

        return db.ejecutar(sql, valores)
