    document.addEventListener('DOMContentLoaded', function () {
        // Récupérer tous les liens des onglets
        const tabLinks = document.querySelectorAll('.nav-link');

        // Ajouter un écouteur d'événement à chaque lien d'onglet
        tabLinks.forEach(function (tabLink) {
            tabLink.addEventListener('click', function (event) {
                event.preventDefault(); // Empêcher le comportement par défaut du lien

                // Récupérer l'ID de la section associée à l'onglet
                const targetId = this.getAttribute('href');

                // Masquer toutes les sections d'onglets
                document.querySelectorAll('.tab-pane').forEach(function (tabContent) {
                    tabContent.classList.remove('show', 'active');
                });

                // Afficher la section cible de l'onglet
                document.querySelector(targetId).classList.add('show', 'active');

                // Retirer la classe 'active' de tous les liens d'onglet
                tabLinks.forEach(function (link) {
                    link.classList.remove('active');
                });

                // Ajouter la classe 'active' au lien d'onglet cliqué
                this.classList.add('active');

                 // Ajouter une classe spécifique pour la couleur orange sur l'onglet sélectionné
                 tabLinks.forEach(function (link) {
                    link.classList.remove('active-tab'); // Supprimer toutes les classes actives
                });
                this.classList.add('active-tab'); // Ajouter la classe active à l'onglet sélectionné
            });
        });
    });
