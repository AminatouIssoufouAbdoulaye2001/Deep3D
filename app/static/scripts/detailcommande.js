$(document).ready(function() {
    $('.voir-details').click(function() {
        var commandeId = $(this).data('commande-id');
        $('#commandeIdModal').text('Détails de la commande N° ' + commandeId);
        $.ajax({
            url: '/get_articles/' + commandeId,
            type: 'GET',
            success: function(response) {
                var articlesHtml = '';
                $.each(response, function(index, article) {
                    articlesHtml += '<tr>';
                    articlesHtml += '<td>' + article.sku + '</td>';
                    articlesHtml += '<td>' + article.largeur + '</td>';
                    articlesHtml += '<td>' + article.longueur + '</td>';
                    articlesHtml += '<td>' + article.hauteur + '</td>';
                    articlesHtml += '<td>' + article.poids + '</td>';
                    articlesHtml += '<td>' + article.quantite + '</td>';
                    articlesHtml += '<td>' + article.fragile + '</td>';
                    articlesHtml += '</tr>';
                });
                $('#articlesList').html(articlesHtml);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('.emballer').click(function() {
        var commandeId = $(this).data('commande-id');
        $.ajax({
            url: '/pack_articles',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ commande_id: commandeId }),
            success: function(data) {
                // Remplir la fenêtre modale avec les données reçues
                var modalTable = $('#myModal').find('.table-container');
                modalTable.empty(); // Vide le contenu précédent
    
                var headers = Object.keys(data[0]);
                var tableHtml = '';
    
                // Générer le contenu du tableau
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Sommaire</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<tbody>';
                tableHtml += '<tr><td>' + headers[0] + '</td><td class="font-weight-bold ar">' + data[0][headers[0]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[1] + '</td><td class="font-weight-bold ar">' + data[0][headers[1]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[2] + '</td><td class="font-weight-bold ar">' + data[0][headers[2]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[3] + '</td><td class="font-weight-bold ar">' + data[0][headers[3]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[4] + '</td><td class="font-weight-bold ar">' + data[0][headers[4]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[5] + '</td><td class="font-weight-bold ar">' + data[0][headers[5]] + '</td></tr>';
                tableHtml += '<tr><td>'+ headers[6] + '</td><td class="font-weight-bold ar">' + data[0][headers[6]] + '</td></tr>';
                tableHtml += '</tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';
    
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Espace utilisé d\'emballage:</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                tableHtml += '<tbody><tr><td>1</td><td class="text-right pr-3"></td></tr></tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';
    
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Article emballé:</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                tableHtml += '<tbody><tr><td>' + data[0][headers[6]] + '</td><td class="text-right pr-3">2</td></tr></tbody>';
                tableHtml += '<tbody><tr><td>' + data[1][headers[6]] + '</td><td class="text-right pr-3">2</td></tr></tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';
    
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Articles non emballés:</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                tableHtml += '<tbody><tr><td>1</td><td class="text-right pr-3"></td></tr></tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';

                tableHtml += '<div>';
                tableHtml += '<div class="font-weight-bold card-box-header mx-3 pb-3">Packing space 1 of 1</div>';
                tableHtml += '<div class="card-box mx-3">';
                tableHtml += '<div class="sku-name text-truncate">SKU: <span class="font-weight-bold">1</span></div>';
                tableHtml += '<div class="img-preview mb-4">';
                tableHtml += '<img src="http://images-eu.api.3dbinpacking.com/f1b9a7e0b50ca846c3cfcde2351e7a57/20240604/fa38f063af40d95d5826b26b1970e53b/1717512946-5099-2988445.svg">';
                tableHtml += '</div>';
                tableHtml += '<table class="form">';
                tableHtml += '<tr><td>Dims:</td><td class="text-right font-weight-bold">50x30x30 [cm]</td></tr>';
                tableHtml += '<tr><td>Used space:</td><td class="text-right font-weight-bold">26.7 %</td></tr>';
                tableHtml += '<tr><td>Stack height:</td><td class="text-right font-weight-bold">20 [cm]</td></tr>';
                tableHtml += '<tr><td>Weight:</td><td class="text-right font-weight-bold">16 [kg]</td></tr>';
                tableHtml += '<tr><td>Net weight:</td><td class="text-right font-weight-bold">6 [kg]</td></tr>';
                tableHtml += '<tr><td>DIM weight:</td><td class="text-right font-weight-bold">0 [kg]</td></tr>';
                tableHtml += '<tr><td>Packed:</td><td class="text-right font-weight-bold">3</td></tr>';
                tableHtml += '</table>';
                tableHtml += '<div class="d-flex my-3 py-2 bg-light border border-secondary-light rounded align-items-center">';
                tableHtml += '<a href="#" class="text-nowrap" data-images-box-id="#box1" style="text-decoration: none; color: #49495e;">';
                tableHtml += '<i class="fas fa-eye text-secondary pr-1 pl-2"></i> Voir l\'emballage';
                tableHtml += '</a>';
                tableHtml += '</div>';
                tableHtml += '<div class="font-weight-bold">Articles emballés:</div>';
                tableHtml += '<table class="form">';
                tableHtml += '<tr><td>SKU001:</td><td class="text-right font-weight-bold">3</td></tr>';
                tableHtml += '</table>';
                tableHtml += '</div>';
                tableHtml += '</div>';
     
                modalTable.html(tableHtml);
    
                // Afficher la fenêtre modale
                $('#myModal').modal('show');
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    
    
});
