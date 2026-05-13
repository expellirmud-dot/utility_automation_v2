(function loadOverview() {
  var container = document.getElementById('overview-cards');

  function addLine(card, label, value) {
    var row = document.createElement('p');
    row.className = 'meta';
    row.textContent = label + ': ' + String(value);
    card.appendChild(row);
  }

  fetch('/ops/api/overview')
    .then(function (response) { return response.json(); })
    .then(function (payload) {
      payload.cards.forEach(function (item) {
        var card = document.createElement('article');
        card.className = 'card';

        var title = document.createElement('h2');
        title.textContent = item.title;

        addLine(card, 'Projection Source', item.projection_source);
        addLine(card, 'Read Only', item.read_only);
        addLine(card, 'Authority Coupled', item.authority_coupled);
        addLine(card, 'Fallback Active', item.fallback_active);
        addLine(card, 'Status', item.status);
        addLine(card, 'Label', item.label);

        card.insertBefore(title, card.firstChild);
        container.appendChild(card);
      });
    });
})();
