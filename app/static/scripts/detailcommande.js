
    $(document).ready(function() {
        $('.voir-details').click(function() {
            var commandeId = $(this).data('commande-id');
            $('#commandeIdModal').text('Détails de la commande N° ' + commandeId);
            $.ajax({
                url: '/get_articles/' + commandeId, // Route Flask pour récupérer les articles associés à la commande
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
                    $('#articlesList').html(articlesHtml); // Affiche les articles dans le tableau
                },
                error: function(error) {
                    console.log(error);
                }
            });
        });
    });


