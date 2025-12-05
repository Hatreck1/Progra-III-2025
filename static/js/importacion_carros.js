document.addEventListener("DOMContentLoaded", function () {

    // ---------------------------
    //  Importación de Carros - Validaciones + Navegación
    // ---------------------------

    let paso = 0;
    const steps = document.querySelectorAll(".wizard-step");
    const progress = document.getElementById("wizardProgressBar");

    function updateWizard() {
        steps.forEach((s, i) => s.classList.toggle("active", i === paso));
        progress.style.width = ((paso + 1) / steps.length * 100) + "%";
    }

    // ---------------------------
    // VALIDACIÓN DE CAMPOS POR PASO
    // ---------------------------
    function validarPasoActual() {
        const currentStep = steps[paso];
        const inputs = currentStep.querySelectorAll("input, select");

        for (let input of inputs) {
            if (input.type !== "file" && !input.value.trim()) {

                Swal.fire({
                    icon: "warning",
                    title: "Campo requerido",
                    text: `Debes completar: ${input.name.replace("_", " ")}`,
                });

                return false;
            }
        }
        return true;
    }

    // ---------------------------
    // BOTONES SIGUIENTE
    // ---------------------------
    document.querySelectorAll(".next-btn").forEach(btn => {
        btn.addEventListener("click", () => {

            if (!validarPasoActual()) return;

            if (paso < steps.length - 1) paso++;
            updateWizard();
        });
    });

    // ---------------------------
    // BOTONES ANTERIOR
    // ---------------------------
    document.querySelectorAll(".prev-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            if (paso > 0) paso--;
            updateWizard();
        });
    });

    // ---------------------------
    // VALIDACIÓN FINAL AL ENVIAR
    // ---------------------------
    document.querySelector("form").addEventListener("submit", function(e) {

        e.preventDefault();

        if (!validarPasoActual()) return;

        Swal.fire({
            icon: "success",
            title: "¡Importación guardada!",
            text: "Todos los datos son correctos.",
            showConfirmButton: false,
            timer: 1500
        }).then(() => {
            e.target.submit();
        });

    });

    updateWizard();
});
