(function opsConsole() {
  var sectionNames = ['Overview', 'Incidents', 'Recovery', 'Simulation', 'Mesh', 'Policy', 'Replay', 'System Health'];
  var activeSection = 'Overview';
  var nav = document.getElementById('section-nav');
  var container = document.getElementById('section-content');
  var sectionTitle = document.getElementById('active-section-title');
  var overviewCache = null;
  var incidentStatusCache = null;
  var incidentListCache = null;

  function clearNode(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }

  function addLine(card, label, value) {
    var row = document.createElement('p');
    row.className = 'meta';
    row.textContent = label + ': ' + String(value);
    card.appendChild(row);
  }

  function addStatusChip(card, state, label) {
    var chip = document.createElement('span');
    chip.className = 'status-chip';
    chip.setAttribute('data-state', state);
    chip.textContent = label;
    card.appendChild(chip);
  }

  function createCard(title) {
    var card = document.createElement('article');
    card.className = 'card';
    var heading = document.createElement('h3');
    heading.textContent = title;
    card.appendChild(heading);
    return card;
  }

  function renderOverview(cards) {
    clearNode(container);
    if (!cards || cards.length === 0) {
      var empty = createCard('Overview Status');
      addStatusChip(empty, 'not_connected', 'Not connected');
      addLine(empty, 'Source', 'Source unavailable');
      container.appendChild(empty);
      return;
    }
    cards.forEach(function (item) {
      var card = createCard(item.title);
      addStatusChip(card, item.status, item.label);
      addLine(card, 'Projection Source', item.projection_source);
      addLine(card, 'Read Only', item.read_only);
      addLine(card, 'Authority Coupled', item.authority_coupled);
      addLine(card, 'Fallback Active', item.fallback_active);
      container.appendChild(card);
    });
  }

  function renderIncidentSection() {
    clearNode(container);
    var summary = createCard('Incident Review Summary');

    if (incidentStatusCache) {
      addStatusChip(summary, incidentStatusCache.status, incidentStatusCache.status_label);
      addLine(summary, 'Projection Source', incidentStatusCache.source_ref);
      addLine(summary, 'Read Only', incidentStatusCache.read_only);
      addLine(summary, 'Authority Coupled', incidentStatusCache.authority_coupled);
      addLine(summary, 'Fallback Active', incidentStatusCache.fallback_active);
    } else {
      addStatusChip(summary, 'not_connected', 'Not connected');
      addLine(summary, 'Projection Source', 'Source unavailable');
    }

    if (incidentListCache) {
      addLine(summary, 'Incident Count', incidentListCache.incidents.length);
    } else {
      addLine(summary, 'Incident Count', 0);
    }
    container.appendChild(summary);

    var preview = createCard('Incident Preview (Read-only)');
    if (!incidentListCache) {
      addStatusChip(preview, 'loading', 'Loading...');
      addLine(preview, 'State', 'Loading...');
      container.appendChild(preview);
      return;
    }
    if (incidentListCache.incidents.length === 0) {
      addStatusChip(preview, 'not_connected', 'No incidents available');
      addLine(preview, 'State', 'No incidents available');
      container.appendChild(preview);
      return;
    }

    incidentListCache.incidents.forEach(function (incident) {
      var item = document.createElement('p');
      item.className = 'meta';
      item.textContent = incident.incident_id + ' | ' + incident.title + ' | ' + incident.severity + ' | ' + incident.status;
      preview.appendChild(item);
    });
    container.appendChild(preview);
  }

  function renderPlaceholder(sectionName) {
    clearNode(container);
    var card = createCard(sectionName + ' Status');
    addStatusChip(card, 'not_connected', 'Not connected');
    addLine(card, 'State', 'Source unavailable');
    container.appendChild(card);
  }

  function renderActiveSection() {
    sectionTitle.textContent = activeSection;
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
      .then(function (payload) { incidentStatusCache = payload; return fetch('/incident-review/api/incidents'); })
      .then(function (response) { return response.json(); })
      .then(function (payload) { incidentListCache = payload; });
  }

  buildNav();
  renderActiveSection();

  fetch('/ops/api/overview')
    .then(function (response) { return response.json(); })
    .then(function (payload) { overviewCache = payload; return fetchIncidents(); })
    .then(function () { renderActiveSection(); })
    .catch(function () {
      incidentStatusCache = null;
      incidentListCache = { incidents: [] };
      renderActiveSection();
    });
})();
