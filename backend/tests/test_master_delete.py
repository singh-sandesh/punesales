"""Tests for iteration 6 — DELETE /api/masters/{kind}/{id} hard vs soft delete + bootstrap filter."""
import os
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope='module')
def client():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s


def _post(client, path, body):
    r = client.post(f"{API}{path}", json=body)
    assert r.status_code == 200, f'{path} -> {r.status_code} {r.text}'
    return r.json()


def _get_ids(client, col):
    r = client.get(f"{API}/bootstrap")
    assert r.status_code == 200
    return {x['id'] for x in r.json()[col]}


# ---------- BRANDS ----------

def test_brand_hard_delete_when_no_products(client):
    brand = _post(client, '/masters/brands', {'name': 'TEST_HardBrand', 'code': 'THB'})
    r = client.delete(f"{API}/masters/brands/{brand['id']}")
    assert r.status_code == 200
    assert r.json() == {'deleted': True}
    assert brand['id'] not in _get_ids(client, 'brands')


def test_brand_soft_delete_when_has_products(client):
    brand = _post(client, '/masters/brands', {'name': 'TEST_SoftBrand', 'code': 'TSB'})
    product = _post(client, '/products', {'name': 'TEST_P', 'brand_id': brand['id'],
                                          'product_type': 'battery'})
    r = client.delete(f"{API}/masters/brands/{brand['id']}")
    assert r.status_code == 200
    assert r.json() == {'deactivated': True}
    assert brand['id'] not in _get_ids(client, 'brands')
    # cleanup product
    client.delete(f"{API}/products/{product['id']}")


# ---------- DEALERS ----------

def test_dealer_hard_delete(client):
    dealer = _post(client, '/masters/dealers', {'name': 'TEST_D1'})
    r = client.delete(f"{API}/masters/dealers/{dealer['id']}")
    assert r.status_code == 200 and r.json() == {'deleted': True}
    assert dealer['id'] not in _get_ids(client, 'dealers')


def test_dealer_soft_delete_with_transaction_and_ledger_resolves_name(client):
    brand = _post(client, '/masters/brands', {'name': 'TEST_BR_D'})
    product = _post(client, '/products', {'name': 'TEST_PD', 'brand_id': brand['id']})
    # Need stock for outward -> do inward first (party_id can be a supplier or none)
    supplier = _post(client, '/masters/suppliers', {'name': 'TEST_SUP_D'})
    _post(client, '/transactions', {'kind': 'inward', 'party_id': supplier['id'],
                                    'items': [{'product_id': product['id'], 'quantity': 5}]})
    dealer = _post(client, '/masters/dealers', {'name': 'TEST_D_LINKED'})
    _post(client, '/transactions', {'kind': 'outward', 'party_id': dealer['id'],
                                    'items': [{'product_id': product['id'], 'quantity': 2}]})
    r = client.delete(f"{API}/masters/dealers/{dealer['id']}")
    assert r.status_code == 200 and r.json() == {'deactivated': True}
    assert dealer['id'] not in _get_ids(client, 'dealers')
    # Ledger still resolves party name
    ledger = client.get(f"{API}/ledger").json()
    matched = [row for row in ledger if row.get('party_id') == dealer['id']]
    assert matched, 'expected ledger row for archived dealer'
    assert matched[0]['party_name'] == 'TEST_D_LINKED'


# ---------- SUPPLIERS ----------

def test_supplier_hard_delete(client):
    sup = _post(client, '/masters/suppliers', {'name': 'TEST_S1'})
    r = client.delete(f"{API}/masters/suppliers/{sup['id']}")
    assert r.status_code == 200 and r.json() == {'deleted': True}


def test_supplier_soft_delete_when_linked(client):
    brand = _post(client, '/masters/brands', {'name': 'TEST_BR_S'})
    product = _post(client, '/products', {'name': 'TEST_PS', 'brand_id': brand['id']})
    sup = _post(client, '/masters/suppliers', {'name': 'TEST_S_LINKED'})
    _post(client, '/transactions', {'kind': 'inward', 'party_id': sup['id'],
                                    'items': [{'product_id': product['id'], 'quantity': 3}]})
    r = client.delete(f"{API}/masters/suppliers/{sup['id']}")
    assert r.status_code == 200 and r.json() == {'deactivated': True}
    assert sup['id'] not in _get_ids(client, 'suppliers')


# ---------- ERROR CASES ----------

def test_invalid_kind_returns_400(client):
    r = client.delete(f"{API}/masters/invalidkind/xyz")
    assert r.status_code == 400


def test_missing_id_returns_404(client):
    r = client.delete(f"{API}/masters/brands/nonexistent-id-123")
    assert r.status_code == 404


# ---------- REGRESSION: existing endpoints still healthy ----------

@pytest.mark.parametrize('path', ['/bootstrap', '/stock', '/dashboard', '/ledger'])
def test_read_endpoints_ok(client, path):
    r = client.get(f"{API}{path}")
    assert r.status_code == 200


def test_transaction_edit_still_works(client):
    brand = _post(client, '/masters/brands', {'name': 'TEST_BR_TX'})
    product = _post(client, '/products', {'name': 'TEST_TX_P', 'brand_id': brand['id']})
    sup = _post(client, '/masters/suppliers', {'name': 'TEST_TX_SUP'})
    tx = _post(client, '/transactions', {'kind': 'inward', 'party_id': sup['id'],
                                         'items': [{'product_id': product['id'], 'quantity': 4}]})
    r = client.put(f"{API}/transactions/{tx['transaction_id']}",
                   json={'kind': 'inward', 'party_id': sup['id'],
                         'items': [{'product_id': product['id'], 'quantity': 6}]})
    assert r.status_code == 200
    assert r.json()['total_quantity'] == 6


def test_admin_reset(client):
    r = client.post(f"{API}/admin/reset")
    assert r.status_code == 200 and r.json() == {'reset': True}
    boot = client.get(f"{API}/bootstrap").json()
    assert boot == {'brands': [], 'products': [], 'suppliers': [], 'dealers': []}
