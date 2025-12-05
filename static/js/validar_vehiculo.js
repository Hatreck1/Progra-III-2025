document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formVehiculo");

    form.addEventListener("submit", function(e) {

        // Obtener valores
        const marca = form.marca.value.trim();
        const modelo = form.modelo.value.trim();
        const anio = parseInt(form.anio.value);
        const color = form.color.value.trim();
        const tipo = form.tipo.value;
        const transmision = form.transmision.value;
        const combustible = form.combustible.value;
        const kilometraje = parseInt(form.kilometraje.value);
        const precioCompra = parseFloat(form.precio_compra.value);
        const precioVenta = parseFloat(form.precio.value);
        const imagen = form.imagen.files[0];

        // Validar Marca
        if (marca.length < 2) {
            alert("La marca debe tener al menos 2 caracteres.");
            e.preventDefault();
            return;
        }

        // Validar Modelo
        if (modelo.length < 2) {
            alert("El modelo debe tener al menos 2 caracteres.");
            e.preventDefault();
            return;
        }

        // Validar Año
        if (anio < 1990 || anio > 2025) {
            alert("El año debe estar entre 1990 y 2025.");
            e.preventDefault();
            return;
        }

        // Validar Color
        if (color.length < 3) {
            alert("El color debe tener al menos 3 caracteres.");
            e.preventDefault();
            return;
        }

        // Validar Selects
        if (tipo === "") {
            alert("Debe seleccionar un tipo de vehículo.");
            e.preventDefault();
            return;
        }

        if (transmision === "") {
            alert("Debe seleccionar la transmisión.");
            e.preventDefault();
            return;
        }

        if (combustible === "") {
            alert("Debe seleccionar el tipo de combustible.");
            e.preventDefault();
            return;
        }

        // Validar Kilometraje
        if (isNaN(kilometraje) || kilometraje < 0) {
            alert("El kilometraje debe ser un número mayor o igual a 0.");
            e.preventDefault();
            return;
        }

        // Validar Precio de compra
        if (isNaN(precioCompra) || precioCompra <= 0) {
            alert("El precio de compra debe ser mayor que 0.");
            e.preventDefault();
            return;
        }

        // Validar Precio de venta
        if (isNaN(precioVenta) || precioVenta <= 0) {
            alert("El precio de venta debe ser mayor que 0.");
            e.preventDefault();
            return;
        }

        // Validar Imagen
        if (!imagen) {
            alert("Debe seleccionar una imagen del vehículo.");
            e.preventDefault();
            return;
        }

        if (!imagen.type.startsWith("image/")) {
            alert("El archivo seleccionado no es una imagen válida.");
            e.preventDefault();
            return;
        }
    });
});
