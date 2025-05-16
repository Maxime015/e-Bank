    document.addEventListener("DOMContentLoaded", function () {
        const transferButtons = document.querySelectorAll(".transfert-btn");
        transferButtons.forEach(button => {
            button.addEventListener("click", function () {
                const transferUrl = this.dataset.url;
                const montant = prompt("Entrez le montant à transférer :");
                const idDestinataire = prompt("Entrez l'ID du compte destinataire :");

                if (montant && idDestinataire) {
                    // Envoyer les données via POST
                    fetch(transferUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCookie("csrftoken")
                        },
                        body: JSON.stringify({
                            montant: montant,
                            id_destinataire: idDestinataire
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        if (data.success) {
                            window.location.reload(); // Rafraîchit la page si succès
                        }
                    })
                    .catch(error => console.error("Erreur:", error));
                } else {
                    alert("Transfert annulé ou informations invalides.");
                }
            });
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

