from fastapi.testclient import TestClient

from src.ui.incident_review.incident_review_api import app

client = TestClient(app)


def test_ops_route_returns_200_and_get_only():
    response = client.get('/ops')
    assert response.status_code == 200
    assert getattr(client, 'post')('/ops').status_code == 405
    assert getattr(client, 'put')('/ops').status_code == 405
    assert getattr(client, 'patch')('/ops').status_code == 405
    assert getattr(client, 'delete')('/ops').status_code == 405


def test_ops_frontend_has_no_forms_or_mutation_labels():
    html = client.get('/ops').text.lower()
    js = client.get('/ops/ops_console.js').text.lower()

    assert '<form' not in html
    for label in ['approve', 'reject', 'retry', 'execute', 'repair', 'promote']:
        assert label not in html
        assert label not in js


def test_ops_frontend_uses_safe_rendering_patterns():
    js = client.get('/ops/ops_console.js').text

    assert 'createElement' in js
    assert 'textContent' in js
    assert 'appendChild' in js
    assert 'innerHTML' not in js


def test_no_mutation_routes_added_for_ops_shell():
    openapi = client.get('/openapi.json').json()
    mutation_methods = {'post', 'put', 'patch', 'delete'}

    for path, spec in openapi.get('paths', {}).items():
        if path.startswith('/ops'):
            assert mutation_methods.isdisjoint(set(spec.keys()))
