document.addEventListener("DOMContentLoaded", () => {
    const tipoBienSelect = document.getElementById("tipo_bien");
    const otroBienContainer = document.getElementById("otro_bien_container");

    if (!tipoBienSelect || !otroBienContainer) return;

    tipoBienSelect.addEventListener("change", function () {
        if (this.value === "otro") {
            otroBienContainer.classList.remove("hidden");
        } else {
            otroBienContainer.classList.add("hidden");
        }
    });
});
