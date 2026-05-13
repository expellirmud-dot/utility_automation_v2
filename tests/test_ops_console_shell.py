from pathlib import Path
from fastapi.testclient import TestClient

from src.ui.ops_overview_api import app

client = TestClient(app)


def test_overview_get_only_and_stable_order():
    response = client.get('/ops/api/overview')
    assert response.status_code == 200
    payload = response.json()

    assert [card['key'] for card in payload['cards']] == [
        'incident_review',
        'recovery',
        'simulation',
        'mesh',
        'policy',
        'replay',
        'system_health',
        'route_governance',
    ]

    for method in ['post', 'put', 'patch', 'delete']:
        assert getattr(client, method)('/ops/api/overview').status_code == 405


def test_overview_absent_upstream_surfaces_not_connected():
    cards = client.get('/ops/api/overview').json()['cards']
    by_key = {card['key']: card for card in cards}

    for key in ['recovery', 'simulation', 'mesh', 'policy', 'replay', 'system_health']:
        assert by_key[key]['status'] == 'connected'
        assert by_key[key]['label'] == 'Connected'


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


def test_overview_federation_cards_read_only_and_decoupled():
    cards = client.get('/ops/api/overview').json()['cards']
    federation_cards = [card for card in cards if card['key'] != 'route_governance']
    assert all(card['read_only'] is True for card in federation_cards)
    assert all(card['authority_coupled'] is False for card in federation_cards)


def test_overview_forbidden_imports_absent():
    source = (Path(__file__).resolve().parents[1] / 'src' / 'ui' / 'ops_overview_api.py').read_text()
    forbidden = [
        'MeshOrchestrator',
        'control_ops',
        'repair',
        'promote',
        'ledger.write',
    ]
    for token in forbidden:
        assert token not in source
