$(document).ready(function(){
    // Fonction pour ajouter le checkbox de visibilité du mot de passe
    function addPasswordToggleCheckbox() {
        // Sélectionnez le champ de mot de passe et son conteneur
        var passwordField = $('.password-input');
        var passwordContainer = passwordField.closest('.form-group');

        // Créez le checkbox de visibilité du mot de passe
        var checkbox = $('<input>').attr('type', 'checkbox').addClass('toggle-password-checkbox');

        // Ajoutez le checkbox à côté du champ de mot de passe, mais initialement caché
        passwordField.after(checkbox);
        checkbox.hide();

        // Fonction pour basculer la visibilité du mot de passe
        function togglePasswordVisibility() {
            if (passwordField.attr('type') === 'password') {
                passwordField.attr('type', 'text');
            } else {
                passwordField.attr('type', 'password');
            }
        }

        // Fonction pour afficher ou masquer le checkbox en fonction de la saisie dans le champ de mot de passe
        function toggleCheckboxVisibility() {
            if (passwordField.val().trim() !== '') {
                checkbox.show();
            } else {
                checkbox.hide();
            }
        }

        // Ajoutez un écouteur d'événements pour détecter les changements de l'état du champ de mot de passe
        passwordField.on('input', function() {
            toggleCheckboxVisibility();
        });

        // Ajoutez un écouteur d'événements pour détecter les changements de l'état du checkbox
        checkbox.on('change', function() {
            togglePasswordVisibility();
        });
    }

    // Appelez la fonction pour ajouter le checkbox lorsque le document est chargé
    addPasswordToggleCheckbox();
});
