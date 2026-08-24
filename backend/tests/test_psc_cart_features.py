"""Backend tests for cart-style PSC single-location stock app."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope='module')
def bootstrap():
    r = requests.get(f"{API}/bootstrap", timeout=15)
    assert r.status_code == 200
    return r.json()


# ---------- bootstrap / dashboard / stock ----------
class TestBootstrap:
    def test_bootstrap_shape(self, bootstrap):
        for k in ('brands', 'products', 'suppliers', 'dealers'):
            assert k in bootstrap and isinstance(bootstrap[k], list)
        assert len(bootstrap['brands']) >= 3

    def test_no_money_fields_in_products(self, bootstrap):
        for p in bootstrap['products']:
            for banned in ('purchase_rate', 'selling_rate', 'rate', 'price', 'inventory_value'):
                assert banned not in p, f"Product carries banned field {banned}: {p}"

    def test_product_type_present(self, bootstrap):
        for p in bootstrap['products']:
            assert p.get('product_type') in ('battery', 'inverter', 'trolley')


class TestDashboard:
    def test_dashboard_counts(self):
        r = requests.get(f"{API}/dashboard")
        assert r.status_code == 200
        d = r.json()
        for k in ('available', 'inward', 'outward',
                 'in_stock_models', 'out_of_stock_models',
                 'low_stock_models', 'total_models', 'transactions'):
            assert k in d, f"Missing {k}"
        for banned in ('inventory_value', 'total_value'):
            assert banned not in d


class TestStock:
    def test_stock_rows_have_product_type(self):
        r = requests.get(f"{API}/stock")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) > 0
        for row in rows:
            assert row.get('product_type') in ('battery', 'inverter', 'trolley')
            for banned in ('rate', 'purchase_rate', 'selling_rate', 'value'):
                assert banned not in row


# ---------- products CRUD ----------
class TestProductLifecycle:
    def test_create_and_delete_product_no_history(self, bootstrap):
        brand_id = bootstrap['brands'][0]['id']
        payload = {'name': 'TEST_Inverter_Delete', 'brand_id': brand_id,
                   'model': 'TDEL', 'capacity': '900VA',
                   'product_type': 'inverter', 'reorder_level': 5}
        r = requests.post(f"{API}/products", json=payload)
        assert r.status_code == 200, r.text
        pid = r.json()['id']
        assert r.json()['product_type'] == 'inverter'

        d = requests.delete(f"{API}/products/{pid}")
        assert d.status_code == 200
        assert d.json() == {'deleted': True}

    def test_create_invalid_product_type_rejected(self, bootstrap):
        brand_id = bootstrap['brands'][0]['id']
        r = requests.post(f"{API}/products", json={
            'name': 'TEST_Bogus', 'brand_id': brand_id, 'product_type': 'ufo'
        })
        assert r.status_code == 400

    def test_delete_product_with_history_archives(self, bootstrap):
        brand_id = bootstrap['brands'][0]['id']
        # create product
        r = requests.post(f"{API}/products", json={
            'name': 'TEST_Archived_Battery', 'brand_id': brand_id,
            'model': 'TARC', 'capacity': '100Ah',
            'product_type': 'battery', 'reorder_level': 10})
        assert r.status_code == 200
        pid = r.json()['id']
        # create a transaction using this product
        tx = requests.post(f"{API}/transactions", json={
            'kind': 'inward', 'party_id': None, 'reference': 'seed',
            'items': [{'product_id': pid, 'quantity': 3}]})
        assert tx.status_code == 200, tx.text
        # delete should archive (deactivate), not remove
        d = requests.delete(f"{API}/products/{pid}")
        assert d.status_code == 200
        assert d.json() == {'deactivated': True}


# ---------- masters ----------
class TestMasters:
    def test_create_brand(self):
        r = requests.post(f"{API}/masters/brands", json={'name': 'TEST_Brand_QA', 'details': {}})
        assert r.status_code == 200
        assert r.json()['name'] == 'TEST_Brand_QA'

    def test_invalid_master_kind(self):
        r = requests.post(f"{API}/masters/warehouses", json={'name': 'x'})
        assert r.status_code == 400


# ---------- transactions ----------
class TestTransactions:
    def test_multi_item_transaction_no_rate(self, bootstrap):
        prods = [p for p in bootstrap['products'] if p.get('active', True)]
        p1, p2 = prods[0], prods[1]
        before = {r['product_id']: r for r in requests.get(f"{API}/stock").json()}
        tx = requests.post(f"{API}/transactions", json={
            'kind': 'inward', 'party_id': None, 'reference': 'TEST_MULTI',
            'items': [{'product_id': p1['id'], 'quantity': 5},
                      {'product_id': p2['id'], 'quantity': 7}]})
        assert tx.status_code == 200, tx.text
        body = tx.json()
        assert body['total_quantity'] == 12
        after = {r['product_id']: r for r in requests.get(f"{API}/stock").json()}
        assert after[p1['id']]['available'] - before[p1['id']]['available'] == 5
        assert after[p2['id']]['available'] - before[p2['id']]['available'] == 7

    def test_outward_rejects_over_available(self, bootstrap):
        p = bootstrap['products'][0]
        r = requests.post(f"{API}/transactions", json={
            'kind': 'outward', 'party_id': None,
            'items': [{'product_id': p['id'], 'quantity': 999999}]})
        assert r.status_code == 400

    def test_edit_transaction_delta_math(self, bootstrap):
        # find an inward tx we can edit
        p = bootstrap['products'][2]
        create = requests.post(f"{API}/transactions", json={
            'kind': 'inward', 'party_id': None, 'reference': 'TEST_EDIT_BASE',
            'items': [{'product_id': p['id'], 'quantity': 10}]})
        assert create.status_code == 200, create.text
        tid = create.json()['transaction_id']
        # Baseline stock
        stock_before = {r['product_id']: r['available']
                        for r in requests.get(f"{API}/stock").json()}
        # decrease qty from 10 -> 4 (delta -6)
        edit = requests.put(f"{API}/transactions/{tid}", json={
            'kind': 'inward', 'party_id': None, 'reference': 'TEST_EDIT_BASE',
            'items': [{'product_id': p['id'], 'quantity': 4}]})
        assert edit.status_code == 200, edit.text
        stock_after = {r['product_id']: r['available']
                       for r in requests.get(f"{API}/stock").json()}
        assert stock_after[p['id']] - stock_before[p['id']] == -6, (
            f"Expected -6 delta got {stock_after[p['id']] - stock_before[p['id']]}")
        # now increase qty from 4 -> 9 (delta +5)
        edit2 = requests.put(f"{API}/transactions/{tid}", json={
            'kind': 'inward', 'party_id': None, 'reference': 'TEST_EDIT_BASE',
            'items': [{'product_id': p['id'], 'quantity': 9}]})
        assert edit2.status_code == 200
        stock_after2 = {r['product_id']: r['available']
                        for r in requests.get(f"{API}/stock").json()}
        assert stock_after2[p['id']] - stock_after[p['id']] == 5


# ---------- dealer profile ----------
class TestDealerProfile:
    def test_profile_returns_summary_no_money(self, bootstrap):
        d = bootstrap['dealers'][0]
        r = requests.get(f"{API}/dealers/{d['id']}/profile")
        assert r.status_code == 200
        body = r.json()
        assert 'summary' in body and 'history' in body and 'dealer' in body
        s = body['summary']
        assert set(s.keys()) == {'total_units', 'total_orders', 'top_brand', 'last_transaction'}
        for h in body['history']:
            assert 'product_type' in h
            for banned in ('rate', 'price', 'value'):
                assert banned not in h


# ---------- ledger ----------
class TestLedger:
    def test_ledger_items_display_has_type(self):
        r = requests.get(f"{API}/ledger")
        assert r.status_code == 200
        for row in r.json():
            for i in row.get('items_display', []):
                assert i.get('product_type') in ('battery', 'inverter', 'trolley')
            for banned in ('rate', 'value', 'total_value'):
                assert banned not in row
