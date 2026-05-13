(function opsConsole() {
  var sectionNames = [
    'Overview',
    'Incidents',
    'Recovery',
    'Simulation',
    'Mesh',
    'Policy',
    'Replay',
    'System Health'
  ];
  var activeSection = 'Overview';
  var nav = document.getElementById('section-nav');
  var container = document.getElementById('section-content');
  var overviewCache = null;
  var incidentStatusCache = null;
  var incidentListCache = null;

  function addLine(card, label, value) {
    var row = document.createElement('p');
    row.className = 'meta';
    row.textContent = label + ': ' + String(value);
    card.appendChild(row);
  }

  function clearNode(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function createCard(title) {
    var card = document.createElement('article');
    card.className = 'card';
    var heading = document.createElement('h2');
    heading.textContent = title;
    card.appendChild(heading);
    return card;
  }

  function renderOverview(cards) {
    clearNode(container);
    cards.forEach(function (item) {
      var card = createCard(item.title);
      addLine(card, 'Projection Source', item.projection_source);
      addLine(card, 'Read Only', item.read_only);
      addLine(card, 'Authority Coupled', item.authority_coupled);
      addLine(card, 'Fallback Active', item.fallback_active);
      addLine(card, 'Status', item.status);
      addLine(card, 'Label', item.label);
      container.appendChild(card);
    });
  }

  function renderIncidentSection() {
    clearNode(container);

    var summary = createCard('Incident Review Summary');
    if (incidentStatusCache) {
      addLine(summary, 'Projection Source', incidentStatusCache.source_ref);
      addLine(summary, 'Read Only', incidentStatusCache.read_only);
      addLine(summary, 'Authority Coupled', incidentStatusCache.authority_coupled);
      addLine(summary, 'Fallback Active', incidentStatusCache.fallback_active);
      addLine(summary, 'Status', incidentStatusCache.status_label);
    } else {
      addLine(summary, 'Status', 'not_connected');
      addLine(summary, 'Label', 'Not connected');
    }

    if (incidentListCache) {
      addLine(summary, 'Incident Count', incidentListCache.incidents.length);
    } else {
      addLine(summary, 'Incident Count', 0);
    }
    container.appendChild(summary);

    if (incidentListCache && incidentListCache.incidents.length > 0) {
      var preview = createCard('Incident Preview');
      incidentListCache.incidents.forEach(function (incident) {
        var item = document.createElement('p');
        item.className = 'meta';
        item.textContent = incident.incident_id + ' | ' + incident.severity + ' | ' + incident.status;
        preview.appendChild(item);
      });
      container.appendChild(preview);
      return;
    }

    var placeholder = createCard('Incident Preview');
    addLine(placeholder, 'Status', 'not_connected');
    addLine(placeholder, 'Label', 'Not connected');
    container.appendChild(placeholder);
  }

  function renderPlaceholder(sectionTitle) {
    clearNode(container);
    var placeholder = createCard(sectionTitle);
    addLine(placeholder, 'Status', 'not_connected');
    addLine(placeholder, 'Label', 'Not connected');
    container.appendChild(placeholder);
  }

  function renderActiveSection() {
    if (activeSection === 'Overview') {
      renderOverview(overviewCache ? overviewCache.cards : []);
      return;
    }
    if (activeSection === 'Incidents') {
      renderIncidentSection();
      return;
    }
    renderPlaceholder(activeSection);
  }

  function setActiveSection(sectionName) {
    activeSection = sectionName;
    var children = nav.children;
    var i = 0;
    while (i < children.length) {
      children[i].setAttribute('data-active', children[i].getAttribute('data-section') === sectionName ? 'true' : 'false');
      i += 1;
    }
    renderActiveSection();
  }

  function buildNav() {
    sectionNames.forEach(function (name) {
      var entry = document.createElement('li');
      entry.className = 'section-item';
      entry.setAttribute('data-section', name);
      entry.setAttribute('data-active', name === activeSection ? 'true' : 'false');
      entry.textContent = name;
      entry.addEventListener('click', function () {
        setActiveSection(name);
      });
      nav.appendChild(entry);
    });
  }

  function fetchIncidents() {
    return fetch('/incident-review/api/source-status')
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        incidentStatusCache = payload;
        return fetch('/incident-review/api/incidents');
      })
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        incidentListCache = payload;
      });
  }

  buildNav();

  fetch('/ops/api/overview')
    .then(function (response) { return response.json(); })
    .then(function (payload) {
      overviewCache = payload;
      return fetchIncidents();
    })
    .then(function () {
      renderActiveSection();
    })
    .catch(function () {
      renderActiveSection();
    });
})();
