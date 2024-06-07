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
                const resultsPage = window.open('', '_blank');
                resultsPage.document.write('<html><head><title>Table des indicateurs</title></head><body>');
                resultsPage.document.write('<h1>Results</h1>');
                resultsPage.document.write('<table border="1">');

                const headers = Object.keys(data[0]);
                resultsPage.document.write('<tr>');
                headers.forEach(header => {
                    resultsPage.document.write('<th>' + header + '</th>');
                });
                resultsPage.document.write('</tr>');

                data.forEach(row => {
                    resultsPage.document.write('<tr>');
                    headers.forEach(header => {
                        resultsPage.document.write('<td>' + row[header] + '</td>');
                    });
                    resultsPage.document.write('</tr>');
                });

                resultsPage.document.write('</table>');
                resultsPage.document.write('</body></html>');
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});
