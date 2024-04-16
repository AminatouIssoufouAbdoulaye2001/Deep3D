
  var ctxCommandes = document.getElementById("commandesChart").getContext("2d");

  fetch('/commandes_by_day')
    .then(response => response.json())
    .then(data => {
      var labels = data.map(entry => entry.day);
      var counts = data.map(entry => entry.count);
  
      var chartData = {
        labels: labels,
        datasets: [{
          label: "Commandes créées par jour",
          data: counts,
          backgroundColor: 'rgba(255, 99, 132, 0.2)', // Couleur de fond
          borderColor: 'rgba(255, 99, 132, 1)', // Couleur de la bordure
          borderWidth: 1 // Largeur de la bordure
        }]
      };
  
      var myLineChartCommandes = new Chart(ctxCommandes, {
        type: 'line',
        data: chartData,
        options: {
          scales: {
            y: {
              beginAtZero: true // Axe Y commence à zéro
            }
          }
        }
      });
    });
  