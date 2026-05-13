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


def test_static_assets_available_and_safe_patterns_present():
    html = client.get('/incident-review').text
    js = client.get('/incident-review/incident_review.js').text

    assert '<form' not in html.lower()
    assert 'button' not in html.lower()

    assert 'fetch(' in js
    assert "fetch('/incident-review/api/incidents')" in js
    assert 'innerHTML' not in js
    assert 'method:' not in js
    assert '.sort(' not in js
    assert '.filter(' not in js
