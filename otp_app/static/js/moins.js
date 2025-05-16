    function confirmerDebiter(compteId, solde) {
        const montant = prompt("Entrez le montant à débiter:", "");
        
        if (montant && parseFloat(montant) > 0 && parseFloat(montant) <= solde) {
            if (confirm("Êtes-vous sûr de vouloir débiter ce montant ?")) {
                // Si confirmation, effectuer l'appel AJAX
                fetch(`/debiter/${compteId}/${montant}/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert("Débit réussi ! Nouveau solde : " + data.new_balance + " $");
                            // Rafraîchissement de la page après succès
                            location.reload();
                        } else {
                            alert("Erreur : " + data.message);
                        }
                    })
                    .catch(error => alert("Une erreur est survenue."));
            }
        } else {
            alert("Montant invalide ou insuffisant.");
        }
    }

