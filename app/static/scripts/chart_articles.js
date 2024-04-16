var ctx = document.getElementById("myChart").getContext("2d");

fetch('/articles_by_day')
  .then(response => response.json())
  .then(data => {
    var labels = data.map(entry => entry.day);
    var counts = data.map(entry => entry.count);

    var chartData = {
      labels: labels,
      datasets: [{
        label: "Articles créés par jour",
        data: counts,
        backgroundColor: 'rgba(75, 192, 192, 0.2)', // Couleur de fond
        borderColor: 'rgba(75, 192, 192, 1)', // Couleur de la bordure
        borderWidth: 1 // Largeur de la bordure
      }]
    };

    var myLineChart = new Chart(ctx, {
      type: 'line',
      data: chartData,
      options: {
        scales: {
          y: {
            beginAtZero: true, // Axe Y commence à zéro
            stepSize: 1 // Incrément entre chaque étiquette
          }
        }
      }
    });
  });

