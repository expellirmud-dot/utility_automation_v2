(function loadIncidents() {
  const container = document.getElementById('incident-list');
  const banner = document.getElementById('source-banner');

  function bannerText(payload) {
    if (payload.source_type === 'runtime_projection') {
      return 'Runtime read-only projection source active.';
    }
    if (payload.source_type === 'snapshot_test') {
      return 'Snapshot test projection source active.';
    }
    return 'File-backed projection fallback active.';
  }

  fetch('/incident-review/api/source-status')
    .then(function (response) {
      return response.json();
    })
    .then(function (payload) {
      banner.textContent = bannerText(payload);
    });

  fetch('/incident-review/api/incidents')
    .then(function (response) {
      return response.json();
    })
    .then(function (payload) {
      payload.incidents.forEach(function (incident) {
        const card = document.createElement('article');
        card.className = 'incident-card';

        const title = document.createElement('h2');
        title.textContent = incident.incident_id + ' — ' + incident.title;

        const meta = document.createElement('p');
        meta.className = 'meta';
        meta.textContent = 'Severity: ' + incident.severity + ' | Status: ' + incident.status;

        const summary = document.createElement('p');
        summary.textContent = incident.summary;

        const note = document.createElement('p');
        note.textContent = 'Operator Note: ' + incident.operator_note;

        card.appendChild(title);
        card.appendChild(meta);
        card.appendChild(summary);
        card.appendChild(note);
        container.appendChild(card);
      });
    });
})();
