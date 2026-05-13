from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app

client = TestClient(app)


def test_overview_get_only_and_stable_order():
    response = client.get('/ops/api/overview')
    assert response.status_code == 200
    payload = response.json()

    assert [card['key'] for card in payload['cards']] == [
        'ops_console',
        'incident_review',
        'recovery_dashboard',
        'simulation_dashboard',
        'telemetry_dashboard',
        'route_governance',
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
    assert by_key['telemetry_dashboard']['status'] == 'not_connected'
    assert by_key['telemetry_dashboard']['label'] == 'Not connected'


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


def test_overview_ops_js_fetches_route_governance_and_no_actions():
    js = client.get('/ops/ops_console.js').text
    assert "fetch('/ops/api/route-governance')" in js
    forbidden_labels = ['approve', 'reject', 'retry', 'execute', 'repair', 'promote']
    for label in forbidden_labels:
        assert label not in js.lower()


def test_overview_renders_route_governance_metadata():
    cards = client.get('/ops/api/overview').json()['cards']
    governance_card = next(card for card in cards if card['key'] == 'route_governance')
    assert governance_card['read_only'] is True
    assert governance_card['authority_coupled'] is False
    assert 'checked_routes=' in governance_card['label']
    assert 'violations=' in governance_card['label']
