$(document).on('click', '.btn-credit', function () {
    const compteId = $(this).data('id');
    const montant = prompt("Entrez le montant à créditer :");

    // Validation du montant saisi
    if (montant) {
        const montantNum = parseFloat(montant);  // Conversion du montant en nombre
        if (!isNaN(montantNum) && montantNum > 0) {
            console.log(`Envoi de la requête pour le compte ${compteId} avec le montant ${montantNum}`);

            $.ajax({
                url: `/crediter/${compteId}/`,
                type: 'POST',
                data: {
                    montant: montantNum,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                success: function (response) {
                    console.log('Réponse reçue :', response);
                    // Affichage du succès avec un message détaillé
                    alert(`Succès : Le montant de ${montantNum} $ a été ajouté. Nouveau solde : ${response.new_balance} $`);
                    // Rafraîchissement de la page après succès
                    location.reload();
                },
                error: function (xhr) {
                    console.error('Erreur reçue :', xhr.responseJSON);
                    // Gestion améliorée de l'erreur avec un message détaillé
                    const errorMessage = xhr.responseJSON?.message || 'Problème inconnu. Veuillez réessayer plus tard.';
                    alert(`Erreur : ${errorMessage}`);
                }
            });
        } else {
            // Si le montant est invalide (non numérique ou <= 0)
            alert("Veuillez entrer un montant valide (positif et numérique).");
        }
    } else {
        // Si aucun montant n'a été saisi
        alert("Vous devez entrer un montant.");
    }
});
