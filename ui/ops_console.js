(function opsConsole() {
  var sectionNames = ['Overview', 'Incidents', 'Recovery', 'Simulation', 'Mesh', 'Policy', 'Replay', 'System Health'];
  var activeSection = 'Overview';
  var nav = document.getElementById('section-nav');
  var titleNode = document.getElementById('content-title');
  var container = document.getElementById('section-content');
  var overviewCache = null;
  var incidentStatusCache = null;
  var incidentListCache = null;
  var routeGovernanceCache = null;

  function addLine(card, label, value) {
    var row = document.createElement('p');
    row.className = 'meta';
    row.textContent = label + ': ' + String(value);
    card.appendChild(row);
  }

  function addStatus(heading, status) {
    var chip = document.createElement('span');
    chip.className = 'status-chip ' + String(status).replace('-', '_');
    chip.textContent = String(status);
    heading.appendChild(chip);
  }

  function clearNode(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function createCard(title, status) {
    var card = document.createElement('article');
    card.className = 'card';
    var heading = document.createElement('h3');
    heading.textContent = title;
    if (status) { addStatus(heading, status); }
    card.appendChild(heading);
    return card;
  }

  function renderOverview(cards) {
    clearNode(container);
    if (!cards || cards.length === 0) {
      var empty = createCard('Overview', 'not_connected');
      addLine(empty, 'Label', 'Source unavailable');
      container.appendChild(empty);
      return;
    }
    cards.forEach(function (item) {
      var card = createCard(item.title, item.status);
      addLine(card, 'Projection Source', item.projection_source);
      addLine(card, 'Read Only', item.read_only);
      addLine(card, 'Authority Coupled', item.authority_coupled);
      addLine(card, 'Fallback Active', item.fallback_active);
      addLine(card, 'Status Label', item.label);
      container.appendChild(card);
    });

    if (routeGovernanceCache) {
      var govCard = createCard('Route Governance', routeGovernanceCache.valid ? 'connected' : 'not_connected');
      addLine(govCard, 'Route Governance', routeGovernanceCache.valid ? 'valid' : 'invalid');
      addLine(govCard, 'Checked Routes', routeGovernanceCache.checked_routes);
      addLine(govCard, 'Violations', (routeGovernanceCache.violations || []).length);
      if (!routeGovernanceCache.valid) {
        addLine(govCard, 'Summary', 'Deterministic violations detected');
      }
      container.appendChild(govCard);
    }
  }

  function renderIncidentSection() {
    clearNode(container);
    var summary = createCard('Incident Review Summary', incidentStatusCache ? 'connected' : 'not_connected');
    if (incidentStatusCache) {
      addLine(summary, 'Projection Source', incidentStatusCache.source_ref);
      addLine(summary, 'Read Only', incidentStatusCache.read_only);
      addLine(summary, 'Authority Coupled', incidentStatusCache.authority_coupled);
      addLine(summary, 'Fallback Active', incidentStatusCache.fallback_active);
      addLine(summary, 'Status', incidentStatusCache.status_label);
    } else {
      addLine(summary, 'Status', 'Not connected');
    }
    addLine(summary, 'Mode', 'Read-only advisory preview');
    addLine(summary, 'Authority', 'No authority coupling');
    container.appendChild(summary);

    var preview = createCard('Incident Preview', incidentListCache ? 'connected' : 'not_connected');
    if (!incidentListCache) {
      addLine(preview, 'Status', 'Loading...');
      container.appendChild(preview);
      return;
    }
    if (!incidentListCache.incidents || incidentListCache.incidents.length === 0) {
      addLine(preview, 'Status', 'No incidents available');
      container.appendChild(preview);
      return;
    }
    incidentListCache.incidents.forEach(function (incident) {
      var item = document.createElement('p');
      item.className = 'meta';
      item.textContent = incident.incident_id + ' | ' + incident.severity + ' | ' + incident.status + ' | ' + incident.title;
      preview.appendChild(item);
    });
    container.appendChild(preview);
  }

  function renderPlaceholder(sectionTitle) {
    clearNode(container);
    var placeholder = createCard(sectionTitle, 'not_connected');
    addLine(placeholder, 'Status', 'Not connected');
    addLine(placeholder, 'Label', 'Source unavailable');
    addLine(placeholder, 'Mode', 'Read-only advisory');
    container.appendChild(placeholder);
  }

  function renderActiveSection() {
    titleNode.textContent = activeSection;
    if (activeSection === 'Overview') { renderOverview(overviewCache ? overviewCache.cards : []); return; }
    if (activeSection === 'Incidents') { renderIncidentSection(); return; }
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
      entry.addEventListener('click', function () { setActiveSection(name); });
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
      .then(function (payload) { incidentListCache = payload; });
  }

  buildNav();
  renderActiveSection();

  fetch('/ops/api/overview')
    .then(function (response) { return response.json(); })
    .then(function (payload) {
      overviewCache = payload;
      return Promise.all([
        fetch('/ops/api/route-governance')
        .then(function (response) { return response.json(); })
        .then(function (governancePayload) {
          routeGovernanceCache = governancePayload;
        })
        .catch(function () { routeGovernanceCache = null; }),
        fetchIncidents().catch(function () {
          incidentStatusCache = null;
          incidentListCache = { incidents: [] };
        }),
      ]);
    })
    .then(function () { renderActiveSection(); })
    .catch(function () {
      incidentStatusCache = null;
      incidentListCache = { incidents: [] };
      renderActiveSection();
    });
})();
