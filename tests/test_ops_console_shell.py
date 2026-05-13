from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app

client = TestClient(app)


def test_overview_get_only_and_stable_order():
    response = client.get('/ops/api/overview')
    assert response.status_code == 200
    payload = response.json()

    assert [card['key'] for card in payload['cards']] == [
        'incident_review',
        'recovery_dashboard',
        'simulation_dashboard',
        'certifier_determinism',
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/overview').status_code == 405


def test_overview_absent_upstream_surfaces_not_connected():
    cards = client.get('/ops/api/overview').json()['cards']
    by_key = {card['key']: card for card in cards}

    assert by_key['recovery_dashboard']['status'] == 'not_connected'
    assert by_key['recovery_dashboard']['label'] == 'Not connected'
    assert by_key['simulation_dashboard']['status'] == 'not_connected'
    assert by_key['simulation_dashboard']['label'] == 'Not connected'
    assert by_key['certifier_determinism']['status'] == 'not_connected'
    assert by_key['certifier_determinism']['label'] == 'Not connected'


def test_ops_shell_static_assets_safe_rendering_read_only():
    html = client.get('/ops').text.lower()
    js = client.get('/ops/ops_console.js').text

    assert '<form' not in html
    assert 'button' not in html

    forbidden_labels = ['approve', 'reject', 'retry', 'execute', 'repair', 'promote']
    for label in forbidden_labels:
        assert label not in html
        assert label not in js.lower()

    assert 'fetch(' in js
    assert "fetch('/ops/api/overview')" in js
    assert 'innerHTML' not in js
    assert 'createElement' in js
    assert 'textContent' in js
    assert 'appendChild' in js
    assert 'method:' not in js
    assert '.sort(' not in js
    assert '.filter(' not in js


def test_ops_shell_read_only_labels_and_no_control_ops_exposure():
    html = client.get('/ops').text
    js = client.get('/ops/ops_console.js').text.lower()

    assert 'Read-only' in html
    assert 'Advisory' in html
    assert 'No authority coupling' in html
    assert 'GET-only' in html
    assert 'loading...' in js
    assert 'no incidents available' in js
    assert 'source unavailable' in js

    assert client.get('/ops/control_ops').status_code == 404
