const emballerButtons = document.querySelectorAll('.emballer');

emballerButtons.forEach(button => {
  button.addEventListener('click', (event) => {
    const commandeId = event.target.dataset.commandeId;

    // Fetch articles associated with the commandeId
    fetchArticles(commandeId);
  });
});

function fetchArticles(commandeId) {
    // Fetch articles from the server
    fetch(`/get-articles/${commandeId}`)
      .then(response => response.json())
      .then(articles => {
        // Process the articles (e.g., convert to JSON format)
        const processedArticles = JSON.stringify(articles);
  
        // Send the processed articles to the packing route
        sendArticlesToPack(processedArticles, commandeId);
      });
  }
  
  function sendArticlesToPack(processedArticles, commandeId) {
    // Use AJAX or Fetch API to send an HTTP POST request to the '/pack-articles' route
    // Include the processedArticles and commandeId in the request body
    // Handle the response from the server
  }
  