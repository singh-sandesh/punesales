"""
PSC Stock Control - Backend API tests (iteration 7).
Covers: empty-state (no demo seed), masters CRUD, transactions with movement_date,
ledger sorting by movement_date desc, edit transaction, inventory math.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://308a932b-412b-4c47-96fb-ee59846aca1e.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

state = {}


@pytest.fixture(scope='module')
def s():
    sess = requests.Session()
    sess.headers.update({'Content-Type': 'application/json'})
    return sess


# --- Empty state / no seed ---
class TestEmptyState:
    def test_bootstrap_empty(self, s):
        r = s.get(f'{API}/bootstrap')
        assert r.status_code == 200
        data = r.json()
        for k in ['brands', 'products', 'suppliers', 'dealers']:
            assert data[k] == [], f'{k} not empty: {data[k]}'

    def test_dashboard_empty(self, s):
        r = s.get(f'{API}/dashboard')
        assert r.status_code == 200
        d = r.json()
        assert d['available'] == 0
        assert d['inward'] == 0
        assert d['outward'] == 0
        assert d['transactions'] == []

    def test_stock_empty(self, s):
        r = s.get(f'{API}/stock')
        assert r.status_code == 200
        assert r.json() == []


# --- Masters + product creation ---
class TestMasters:
    def test_create_brand(self, s):
        r = s.post(f'{API}/masters/brands', json={'name': 'TEST_Brand_A', 'code': 'TBA'})
        assert r.status_code == 200
        d = r.json()
        assert d['name'] == 'TEST_Brand_A'
        assert 'id' in d
        state['brand_id'] = d['id']

    def test_create_product(self, s):
        r = s.post(f'{API}/products', json={
            'name': 'TEST Battery 150Ah',
            'brand_id': state['brand_id'],
            'model': 'TBA-150',
            'capacity': '150Ah',
            'product_type': 'battery',
            'reorder_level': 5,
        })
        assert r.status_code == 200
        d = r.json()
        assert d['brand_id'] == state['brand_id']
        state['product_id'] = d['id']

    def test_create_supplier(self, s):
        r = s.post(f'{API}/masters/suppliers', json={'name': 'TEST_Supplier_1'})
        assert r.status_code == 200
        state['supplier_id'] = r.json()['id']

    def test_create_dealer(self, s):
        r = s.post(f'{API}/masters/dealers', json={'name': 'TEST_Dealer_1'})
        assert r.status_code == 200
        state['dealer_id'] = r.json()['id']

    def test_bootstrap_reflects(self, s):
        d = s.get(f'{API}/bootstrap').json()
        assert any(b['id'] == state['brand_id'] for b in d['brands'])
        assert any(p['id'] == state['product_id'] for p in d['products'])
        assert any(x['id'] == state['supplier_id'] for x in d['suppliers'])
        assert any(x['id'] == state['dealer_id'] for x in d['dealers'])


# --- Transactions with movement_date ---
class TestTransactions:
    def test_inward_with_date(self, s):
        r = s.post(f'{API}/transactions', json={
            'kind': 'inward',
            'party_id': state['supplier_id'],
            'reference': 'TEST-IN-1',
            'movement_date': '2025-01-15',
            'items': [{'product_id': state['product_id'], 'quantity': 50}],
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d['movement_date'] == '2025-01-15'
        state['tx1_id'] = d['transaction_id']

    def test_outward_with_date(self, s):
        r = s.post(f'{API}/transactions', json={
            'kind': 'outward',
            'party_id': state['dealer_id'],
            'movement_date': '2025-06-20',
            'items': [{'product_id': state['product_id'], 'quantity': 10}],
        })
        assert r.status_code == 200, r.text
        assert r.json()['movement_date'] == '2025-06-20'
        state['tx2_id'] = r.json()['transaction_id']

    def test_third_newest(self, s):
        r = s.post(f'{API}/transactions', json={
            'kind': 'inward',
            'party_id': state['supplier_id'],
            'movement_date': '2026-02-05',
            'items': [{'product_id': state['product_id'], 'quantity': 5}],
        })
        assert r.status_code == 200
        state['tx3_id'] = r.json()['transaction_id']

    def test_ledger_sorted(self, s):
        r = s.get(f'{API}/ledger')
        assert r.status_code == 200
        rows = r.json()
        # Filter only test rows we created
        ours = [x for x in rows if x['transaction_id'] in
                {state['tx1_id'], state['tx2_id'], state['tx3_id']}]
        assert len(ours) == 3
        dates = [x['movement_date'] for x in ours]
        assert dates == ['2026-02-05', '2025-06-20', '2025-01-15'], f'Bad order: {dates}'

    def test_edit_transaction_updates_date(self, s):
        r = s.put(f"{API}/transactions/{state['tx1_id']}", json={
            'kind': 'inward',
            'party_id': state['supplier_id'],
            'reference': 'TEST-IN-1-edit',
            'movement_date': '2025-03-10',
            'items': [{'product_id': state['product_id'], 'quantity': 50}],
        })
        assert r.status_code == 200, r.text
        assert r.json()['movement_date'] == '2025-03-10'

    def test_stock_math(self, s):
        # Inward 50 + 5 = 55, outward 10, available = 45
        r = s.get(f'{API}/stock')
        assert r.status_code == 200
        rows = [x for x in r.json() if x['product_id'] == state['product_id']]
        assert len(rows) == 1
        row = rows[0]
        assert row['available'] == 45, row
        assert row['inward'] == 55, row
        assert row['outward'] == 10, row


# --- Cleanup: reset all so DB stays clean for next iteration ---
class TestCleanup:
    def test_reset(self, s):
        r = s.post(f'{API}/admin/reset')
        assert r.status_code == 200
        assert s.get(f'{API}/bootstrap').json() == {
            'brands': [], 'products': [], 'suppliers': [], 'dealers': []}
