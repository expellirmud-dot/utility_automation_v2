(function bootOpsShell() {
  const navLabels = [
    'Overview',
    'Incidents',
    'Recovery',
    'Simulation',
    'Mesh',
    'Policy',
    'Replay',
    'System Health'
  ];

  const navList = document.getElementById('ops-nav-list');
  const cards = document.getElementById('summary-cards');
  const status = document.getElementById('ops-source-status');

  navLabels.forEach(function (label) {
    const item = document.createElement('li');
    item.textContent = label;
    navList.appendChild(item);
  });

  function renderCard(title, value) {
    const card = document.createElement('article');
    card.className = 'summary-card';

    const heading = document.createElement('h3');
    heading.textContent = title;

    const body = document.createElement('p');
    body.textContent = value;

    card.appendChild(heading);
    card.appendChild(body);
    cards.appendChild(card);
  }

  fetch('/incident-review/api/source-status')
    .then(function (response) { return response.json(); })
    .then(function (payload) {
      status.textContent = 'Source: ' + payload.status_label + ' | Read-only: ' + String(payload.read_only);
      renderCard('Projection Source', payload.source_type);
      renderCard('Status Label', payload.status_label);
      renderCard('Authority Coupled', String(payload.authority_coupled));
      renderCard('Fallback Active', String(payload.fallback_active));
    });
})();
