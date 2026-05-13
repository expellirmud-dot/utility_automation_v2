from fastapi.testclient import TestClient

from src.ui.incident_review.incident_review_api import app

client = TestClient(app)


def test_get_incidents_read_only_and_deterministic_order():
    response = client.get('/incident-review/api/incidents')
    assert response.status_code == 200
    payload = response.json()
    assert [item['incident_id'] for item in payload['incidents']] == [
        'INC-1001',
        'INC-1002',
        'INC-1003',
    ]


def test_non_get_methods_not_allowed():
    for method in ['post', 'put', 'patch', 'delete']:
        response = getattr(client, method)('/incident-review/api/incidents')
        assert response.status_code == 405


def test_stable_serialization_and_projection_panels_present():
    payload = client.get('/incident-review/api/incidents').json()
    first = payload['incidents'][0]
    assert list(first.keys()) == [
        'incident_id',
        'title',
        'severity',
        'status',
        'summary',
        'operator_note',
    ]
    assert 'replay=' in first['summary']
    assert 'policyImpact=' in first['summary']
    assert 'health=' in first['summary']
    assert 'lineage=' in first['operator_note']


def test_static_assets_available_and_safe_patterns_present():
    html = client.get('/incident-review').text
    js = client.get('/incident-review/incident_review.js').text

    assert '<form' not in html.lower()
    assert 'button' not in html.lower()

    assert 'fetch(' in js
    assert "fetch('/incident-review/api/incidents')" in js
    assert "fetch('/incident-review/api/source-status')" in js
    assert 'innerHTML' not in js
    assert 'method:' not in js
    assert '.sort(' not in js
    assert '.filter(' not in js


def test_source_status_get_only_and_deterministic_shape():
    response = client.get('/incident-review/api/source-status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['read_only'] is True
    assert payload['authority_coupled'] is False
    assert payload['fallback_active'] is True
    assert payload['source_type'] == 'file_projection'
    assert payload['status_label'] == 'file_projection_fallback'
    assert 'source_path' in payload

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/incident-review/api/source-status').status_code == 405
