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
  var domainPanelCache = {};
  var domainPanelLoadFailed = false;

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
    var keyBySection = {
      Recovery: 'recovery',
      Simulation: 'simulation',
      Mesh: 'mesh',
      Policy: 'policy',
      Replay: 'replay',
      'System Health': 'system-health'
    };
    var panelKey = keyBySection[sectionTitle];
    if (panelKey && domainPanelCache[panelKey]) {
      clearNode(container);
      var livePanel = createCard(sectionTitle, domainPanelCache[panelKey].status);
      addLine(livePanel, 'Source', domainPanelCache[panelKey].source);
      addLine(livePanel, 'Mode', 'Read-only advisory');
      addLine(livePanel, 'Advisory Only', domainPanelCache[panelKey].advisory_only);
      addLine(livePanel, 'Item Count', domainPanelCache[panelKey].item_count);
      addLine(livePanel, 'Ordering', (domainPanelCache[panelKey].metadata || {}).deterministic_ordering || 'unknown');
      if (!domainPanelCache[panelKey].items || domainPanelCache[panelKey].items.length === 0) {
        addLine(livePanel, 'Items', 'No items available');
        if (domainPanelCache[panelKey].diagnostics && domainPanelCache[panelKey].diagnostics.length > 0) {
          addLine(livePanel, 'Diagnostics', domainPanelCache[panelKey].diagnostics[0].code || 'degraded');
        }
      } else {
        domainPanelCache[panelKey].items.forEach(function (entry) {
          var row = document.createElement('p');
          row.className = 'meta';
          row.textContent = String(entry.id || 'unknown_id');
          livePanel.appendChild(row);
        });
      }
      container.appendChild(livePanel);
      return;
    }
    if (panelKey && domainPanelLoadFailed) {
      clearNode(container);
      var degraded = createCard(sectionTitle, 'degraded');
      addLine(degraded, 'Status', 'degraded');
      addLine(degraded, 'Label', 'Domain panel source unavailable');
      addLine(degraded, 'Mode', 'Read-only advisory');
      container.appendChild(degraded);
      return;
    }
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

  function fetchDomainPanels() {
    var endpoints = ['/ops/api/recovery', '/ops/api/simulation', '/ops/api/mesh', '/ops/api/policy', '/ops/api/replay', '/ops/api/system-health'];
    return Promise.all(endpoints.map(function (endpoint) {
      return fetch(endpoint)
        .then(function (response) { return response.json(); })
        .then(function (payload) { domainPanelCache[endpoint.replace('/ops/api/', '')] = payload; });
    })).catch(function () {
      domainPanelLoadFailed = true;
    });
  }

  buildNav();
  renderActiveSection();

  fetch('/ops/api/overview')
    .then(function (response) { return response.json(); })
    .then(function (payload) {
      overviewCache = payload;
      return fetch('/ops/api/route-governance')
        .then(function (response) { return response.json(); })
        .then(function (governancePayload) {
          routeGovernanceCache = governancePayload;
          return fetchIncidents().then(function () { return fetchDomainPanels(); });
        });
    })
    .then(function () { renderActiveSection(); })
    .catch(function () {
      incidentStatusCache = null;
      incidentListCache = { incidents: [] };
      renderActiveSection();
    });
})();
