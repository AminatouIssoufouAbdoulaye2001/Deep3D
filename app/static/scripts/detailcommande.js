$(document).ready(function() {
    // Gestion du modal pour le bouton 'emballer'
    document.querySelectorAll('.emballer').forEach(function(button) {
        button.addEventListener('click', function() {
            var commandeId = this.getAttribute('data-commande-id');
            var modal = new bootstrap.Modal(document.getElementById('myModal'));
            document.getElementById('saveButton').setAttribute('data-commande-id', commandeId);
            modal.show();
        });
    });

    // Gestion du clic sur le bouton 'Enregistrer'
    document.getElementById('saveButton').addEventListener('click', function() {
        var commandeId = this.getAttribute('data-commande-id');
        
        fetch('/update_commande_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: commandeId, status: 'Emballer' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload(); // Recharger la page pour afficher le message flash
            } else {
                alert('Erreur lors de la mise à jour du statut: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Erreur lors de la requête:', error);
            alert('Erreur lors de la requête. Veuillez réessayer plus tard.');
        });
    });

    // Gestion du clic sur 'Voir détails'
    $('.voir-details').click(function() {
        var commandeId = $(this).data('commande-id');
        $('#commandeIdModal').text('Détails de la commande N° ' + commandeId);

        $.ajax({
            url: '/get_articles/' + commandeId,
            type: 'GET',
            success: function(response) {
                var articlesHtml = '';
                $.each(response, function(index, article) {
                    articlesHtml += `
                        <tr>
                            <td>${article.sku}</td>
                            <td>${article.largeur}</td>
                            <td>${article.longueur}</td>
                            <td>${article.hauteur}</td>
                            <td>${article.poids}</td>
                            <td>${article.quantite}</td>
                            <td>${article.fragile}</td>
                        </tr>`;
                });
                $('#articlesList').html(articlesHtml);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    // Gestion du clic sur 'Emballer'
    $('.emballer').click(function() {
        var commandeId = $(this).data('commande-id');

        $.ajax({
            url: '/pack_articles',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ commande_id: commandeId }),
            success: function(data) {
                var modalTable = $('#myModal').find('.table-container');
                modalTable.empty();

                // Utiliser les valeurs définies pour les colonnes
                var headers1 = {
                    sku: "sku",  
                    id_bin: 'ID Carton', 
                    item_L: 'Longueur Article (cm)',
                    item_l: 'Largeur Article (cm)', 
                    item_h: 'Hauteur Article (cm)', 
                    item_qte: 'Quantite Article', 
                    item_v: "Volume Article",
                    items_v: "Volume Articles",
                    items_weight: "Poids Articles",
                    bin_poids_max: 'Poids_max Carton (kg)', 
                    prix: 'Prix',
                    bin_type: 'Type',
                    bin_v: "Volume Carton",
                    esp_inoc: 'Espace inoccupé', 
                    w_inoc: 'Poids inoccupé',
                    item_q: 'Quantite_key',
                    bin_q: 'Quantite Carton',
                    bin_L: 'Longueur Carton (cm)',
                    bin_l: 'Largeur Carton (cm)',
                    bin_h: 'Hauteur Carton (cm)',
                    nb_bin : "nb_bin",
                };

                // Calculs des pourcentages et poids restants
                const poids_restant1 = (data[0][headers1.bin_poids_max] - data[0][headers1.items_weight]).toFixed(2);
                const percentageResult = ((1 - parseFloat(data[0][headers1.esp_inoc]) / 100) * 100).toFixed(2) + ' %';
                const percentageResults = ((1 - parseFloat(data[0][headers1.w_inoc]) / 100) * 100).toFixed(2) + ' %';



                var tableHtml = '';
    
                // Générer le contenu du tableau
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Sommaire</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<tbody>';
                tableHtml += '<tr><td>' + headers1.esp_inoc + '</td><td class="font-weight-bold ar">' + data[0][headers1.esp_inoc] + ' %</td></tr>';
                tableHtml += '<tr><td>' + headers1.bin_v + '</td><td class="font-weight-bold ar">' + data[0][headers1.bin_v] + '</td></tr>';
                tableHtml += '<tr><td>' + headers1.items_v + '</td><td class="font-weight-bold ar">' + data[0][headers1.items_v] + '</td></tr>';
                tableHtml += '<tr><td>' + headers1.prix + '</td><td class="font-weight-bold ar">' + data[0][headers1.prix] + '</td></tr>';
                tableHtml += '<tr><td>' + headers1.items_weight + '</td><td class="font-weight-bold ar">' + data[0][headers1.items_weight] + '</td></tr>';
                tableHtml += '<tr><td>' + headers1.bin_poids_max + '</td><td class="font-weight-bold ar">' + data[0][headers1.bin_poids_max] + '</td></tr>';
                tableHtml += '<tr><td>' + headers1.w_inoc + '</td><td class="font-weight-bold ar">' + data[0][headers1.w_inoc] + ' %</td></tr>';
                tableHtml += '</tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';
    
                // Générer le contenu pour les conteneurs utilisés
                //tableHtml += '<div class="table-wrapper">';
                //tableHtml += '<div class="text-18 mb-4">Conteneurs utilisés:</div>';
                //tableHtml += '<table class="form simple gray table-bordered">';
                //tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                //tableHtml += '<tbody>';
    
                // Collecter des valeurs uniques pour les conteneurs
                var uniqueContainers = new Set();
                data.forEach(function(item) {
                    if (item[headers1.id_bin]) {
                        uniqueContainers.add(item[headers1.id_bin]);
                    }
                });

                // Afficher les conteneurs utilisés, qu'il y en ait un ou plusieurs
                if (uniqueContainers.size > 0) {
                    tableHtml += '<div class="table-wrapper">';
                    tableHtml += '<div class="text-18 mb-4">Conteneur(s) utilisé(s):</div>';
                    tableHtml += '<table class="form simple gray table-bordered">';
                    tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                    tableHtml += '<tbody>';
                    
                    uniqueContainers.forEach(function(containerId) {
                        var containerData = data.find(item => item[headers1.id_bin] === containerId);
                        tableHtml += '<tr><td>' + containerId + '</td><td class="text-right pr-3">' + containerData[headers1.bin_q] + '</td></tr>';
                    });
                    
                    tableHtml += '</tbody>';
                    tableHtml += '</table>';
                    tableHtml += '</div>';
                }
    
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Article emballé:</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                // Collecter des valeurs uniques
                var uniqueData = [];
                var seen = new Set();

                data.forEach(function(item) {
                    var sku = item[headers1.sku];
                    if (!seen.has(sku)) {
                    seen.add(sku);
                    uniqueData.push(item);
                    }
                });
                uniqueData.forEach(function(item, index) {
                    if (index != uniqueData.length - 1) {
                    tableHtml += '<tr><td>' + item[headers1.sku] + '</td><td class="text-right pr-3">' + item[headers1.item_q] + '</td></tr>';
                    }
                });
                //tableHtml += '<tbody><tr><td>' + data[0][headers1.sku] + '</td><td class="text-right pr-3">' + data[0][headers1.item_q] + '</td></tr></tbody>';
                //tableHtml += '<tbody><tr><td>' + data[5][headers1.sku] + '</td><td class="text-right pr-3">' + data[5][headers1.item_q] + '</td></tr></tbody>';
                //tableHtml += '<tbody><tr><td>' + data[2][headers1.sku] + '</td><td class="text-right pr-3">' + data[2][headers1.item_q] + '</td></tr></tbody>';
                //tableHtml += '<tbody><tr><td>' + data[6][headers1.sku] + '</td><td class="text-right pr-3">' + data[6][headers1.item_q] + '</td></tr></tbody>';
                tableHtml += '</table>';
                tableHtml += '</div>';
    
                tableHtml += '<div class="table-wrapper">';
                tableHtml += '<div class="text-18 mb-4">Articles non emballés:</div>';
                tableHtml += '<table class="form simple gray table-bordered">';
                tableHtml += '<thead><tr><th>ID</th><th>Quantité</th></tr></thead>';
                //tableHtml += '<tbody><tr><td>1</td><td class="text-right pr-3"></td></tr></tbody>';

                const lastItem = data[data.length - 1]; // Dernier élément du tableau

                // Vérifier si le dernier élément contient des articles non emballés
                if (lastItem.non_pack_articles && lastItem.non_pack_articles > 0) {
                    // Parcourir les articles non emballés et afficher leur ID et quantité
                    lastItem.sku.forEach((sku, index) => {
                        const quantity = lastItem.qte[index];
                        tableHtml += `<tr><td>${sku}</td><td class="text-right pr-3">${quantity}</td></tr>`;
                    });
                } else
                {
                    tableHtml += `<tr><td>pas d'articles non emballés</td><td class="text-right pr-3"></td></tr>`;

                }

                tableHtml += '</table>';
                tableHtml += '</div>';
             
        
                // Générer le contenu pour chaque conteneur
                uniqueContainers.forEach(function(containerId) {
                    var containerData = data.find(item => item[headers1.id_bin] === containerId);
                    
                    // Calculs des pourcentages et poids restants
                    const poids_restant1 = (containerData[headers1.bin_poids_max] - containerData[headers1.items_weight]).toFixed(2);
                    const percentageResult = ((1 - parseFloat(containerData[headers1.esp_inoc]) / 100) * 100).toFixed(2) + ' %';
                    const percentageResults = ((1 - parseFloat(containerData[headers1.w_inoc]) / 100) * 100).toFixed(2) + ' %';

                    tableHtml += '<div>';
                    tableHtml += '<div class="card-box mx-3">';
                    tableHtml += '<div class="sku-name text-truncate">ID Carton: <span class="font-weight-bold">' + containerId + '</span></div>';
                    tableHtml += '<div class="img-preview mb-4">';
                    tableHtml += '</div>';
                    tableHtml += '<table class="form">';
                    tableHtml += '<tr><td>Dimensions bin:</td><td class="text-right font-weight-bold">'+containerData[headers1.bin_L]+'x'+containerData[headers1.bin_l]+'x'+containerData[headers1.bin_h]+' [cm]</td></tr>';
                    tableHtml += '<tr><td>Espace occupé:</td><td class="text-right font-weight-bold">'+percentageResult+'</td></tr>';
                    tableHtml += '<tr><td>Poids occupé:</td><td class="text-right font-weight-bold">'+percentageResults+'</td></tr>';
                    tableHtml += '<tr><td>Pile hauteur:</td><td class="text-right font-weight-bold">'+containerData[headers1.bin_L]+' [cm]</td></tr>';
                    tableHtml += '<tr><td>Poids maximum:</td><td class="text-right font-weight-bold">'+containerData[headers1.bin_poids_max]+' [kg]</td></tr>';
                    tableHtml += '<tr><td>Poids net:</td><td class="text-right font-weight-bold">'+containerData[headers1.items_weight]+' [kg]</td></tr>';
                    tableHtml += '<tr><td>poids restant :</td><td class="text-right font-weight-bold">'+poids_restant1+' [kg]</td></tr>';
                    tableHtml += '<tr><td>Type bin :</td><td class="text-right font-weight-bold">'+containerData[headers1.bin_type]+'</td></tr>';
                    tableHtml += '</table>';
                    tableHtml += '<div class="d-flex my-3 py-2 bg-light border border-secondary-light rounded align-items-center">';
                    tableHtml += '<iframe src="/static/images/images_emballage/viz_carton' + containerId + '.html" class="text-nowrap" data-images-box-id="#box1" style="width:850px; height:600px; border:none;"></iframe>';
                    tableHtml += '</div>';
                    
                    // Ajout du bouton de téléchargement du rapport
                    tableHtml += '<div class="mt-3">';
                    tableHtml += '<button class="btn btn-primary download-report" data-container-id="' + containerId + '">Télécharger le rapport</button>';
                    tableHtml += '</div>';
                    
                    tableHtml += '</div>';
                    tableHtml += '</div>';
                });

                modalTable.html(tableHtml);

                // Afficher la fenêtre modale
                $('#myModal').modal('show');

                // Gestion du clic sur le bouton de téléchargement du rapport
                $('.download-report').click(function() {
                    var containerId = $(this).data('container-id');
                    var containerData = data.find(item => item[headers1.id_bin] === containerId);
                    generatePDFReport(containerData, headers1);
                });


            },
            error: function(error) {
                console.log(error);
            }
            });
        });


    // Fonction pour générer et télécharger le rapport PDF
    function generatePDFReport(containerData, headers1) {
        // Créer une nouvelle instance de jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Ajouter le contenu textuel au PDF
        doc.setFontSize(16);
        doc.text('Rapport d\'emballage', 105, 15, null, null, 'center');
        doc.setFontSize(12);
        doc.text('Conteneur ' + containerData[headers1.id_bin], 105, 25, null, null, 'center');

        doc.setFontSize(10);
        let yPosition = 40;
        doc.text('Dimensions: ' + containerData[headers1.bin_L] + 'x' + containerData[headers1.bin_l] + 'x' + containerData[headers1.bin_h] + ' cm', 20, yPosition);
        yPosition += 10;
        doc.text('Espace occupé: ' + ((1 - parseFloat(containerData[headers1.esp_inoc]) / 100) * 100).toFixed(2) + '%', 20, yPosition);
        yPosition += 10;
        doc.text('Poids occupé: ' + ((1 - parseFloat(containerData[headers1.w_inoc]) / 100) * 100).toFixed(2) + '%', 20, yPosition);
        yPosition += 10;
        doc.text('Pile hauteur: ' + containerData[headers1.bin_L] + ' cm', 20, yPosition);
        yPosition += 10;
        doc.text('Poids maximum: ' + containerData[headers1.bin_poids_max] + ' kg', 20, yPosition);
        yPosition += 10;
        doc.text('Poids net: ' + containerData[headers1.items_weight] + ' kg', 20, yPosition);
        yPosition += 10;
        doc.text('Poids restant: ' + (containerData[headers1.bin_poids_max] - containerData[headers1.items_weight]).toFixed(2) + ' kg', 20, yPosition);
        yPosition += 10;
        doc.text('Type de conteneur: ' + containerData[headers1.bin_type], 20, yPosition);

        // Capturer l'image de visualisation
        var iframe = document.querySelector('iframe[src*="viz_carton' + containerData[headers1.id_bin] + '"]');
        if (iframe) {
            html2canvas(iframe.contentDocument.body).then(canvas => {
                // Ajouter l'image au PDF
                var imgData = canvas.toDataURL('image/png');
                doc.addImage(imgData, 'PNG', 15, 120, 180, 120);

                // Sauvegarder le PDF
                doc.save('rapport_emballage_' + containerData[headers1.id_bin] + '.pdf');
            });
        } else {
            // Si l'iframe n'est pas trouvée, sauvegarder le PDF sans l'image
            doc.save('rapport_emballage_' + containerData[headers1.id_bin] + '.pdf');
        }
    }

            // Lorsque le modal se ferme, recharge la page
            $('#myModal').on('hidden.bs.modal', function () {
                location.reload(); // Recharge la page pour afficher les modifications
            });

        });
