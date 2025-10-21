var accion = "nuevo",
    idUsuario = 0;

document.addEventListener("DOMContentLoaded", event => { 
    frmUsuarios.addEventListener("submit", e => {
        e.preventDefault();
        guardarUsuarios();
    });
    obtenerUsuarios();
});

async function guardarUsuarios() {
    let datos = {
        accion,
        idUsuario,
        usuario: txtUsuario.value,
        clave: txtClave.value,
        nombre: txtNombreUsuario.value,
        direccion: txtDireccion.value,
        telefono: txtTelefono.value
    };

    let response = await fetch("/usuarios", {
        method: "POST",
        body: JSON.stringify(datos),
    });

    let respuesta = await response.json();

    if (respuesta.msg != "ok") {
        alertify.error(`Error al procesar usuario: ${respuesta.msg}`);
        return;
    }

    limpiarFormulario();
    obtenerUsuarios();
}

function limpiarFormulario() {
    accion = "nuevo";
    idUsuario = 0;
    txtUsuario.value = "";
    txtClave.value = "";
    txtNombreUsuario.value = "";
    txtDireccion.value = "";
    txtTelefono.value = "";
}

async function obtenerUsuarios() {
    let response = await fetch("/usuarios");
    let respuesta = await response.json();
    mostrarDatosUsuarios(respuesta);
}

function mostrarDatosUsuarios(usuarios) {
    let filas = "";
    usuarios.forEach(usuario => {
        filas += `
            <tr onClick='mostrarUsuario(${JSON.stringify(usuario)})'>
                <td>${usuario.usuario}</td>
                <td>${usuario.nombre}</td>
                <td>${usuario.direccion}</td>
                <td>${usuario.telefono}</td>
                <td><button onClick='eliminarUsuario(${JSON.stringify(usuario)}, event)' class="btn btn-danger btn-sm">ELIMINAR</button></td>
            </tr>
        `;
    });
    tblUsuarios.innerHTML = filas;
}

function mostrarUsuario(usuario) {
    accion = "modificar";
    idUsuario = usuario.idUsuario;
    txtUsuario.value = usuario.usuario;
    txtClave.value = usuario.clave;
    txtNombreUsuario.value = usuario.nombre;
    txtDireccion.value = usuario.direccion;
    txtTelefono.value = usuario.telefono;
}

function eliminarUsuario(usuario, event) {
    event.preventDefault();

    if (confirm(`¿Seguro que desea eliminar al usuario ${usuario.usuario}?`)) {
        idUsuario = usuario.idUsuario;
        accion = "eliminar";
        guardarUsuarios();
    }
}
