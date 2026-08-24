"""PSC iteration 4 backend tests: bootstrap, dashboard, stock, suppliers profile, reset, edit-delta."""
import os
import uuid
import time
import requests
import pytest


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def bootstrap():
    r = requests.get(f"{API}/bootstrap", timeout=15)
    assert r.status_code == 200
    return r.json()


# --- Bootstrap / Dashboard / Stock shape tests ---
def test_bootstrap_shape(bootstrap):
    assert set(["brands", "products", "suppliers", "dealers"]).issubset(bootstrap.keys())
    # no warehouses key expected
    assert "warehouses" not in bootstrap
    assert len(bootstrap["brands"]) >= 3
    assert len(bootstrap["products"]) >= 13
    assert len(bootstrap["suppliers"]) >= 3
    assert len(bootstrap["dealers"]) >= 3
    for p in bootstrap["products"]:
        assert "product_type" in p
        assert p["product_type"] in {"battery", "inverter", "trolley"}


def test_dashboard_shape():
    r = requests.get(f"{API}/dashboard", timeout=15)
    assert r.status_code == 200
    d = r.json()
    for k in ["in_stock_models", "out_of_stock_models", "low_stock_models", "total_models", "available", "inward", "outward", "transactions"]:
        assert k in d, f"Missing {k}"
    assert d["total_models"] >= 13


def test_stock_shape():
    r = requests.get(f"{API}/stock", timeout=15)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 13
    for row in rows:
        assert "product_type" in row
        assert "brand_id" in row
        assert "product_id" in row
        assert "available" in row
        # money-free
        assert "rate" not in row
        assert "purchase_rate" not in row


# --- Supplier profile ---
def test_supplier_profile(bootstrap):
    sup = bootstrap["suppliers"][0]
    r = requests.get(f"{API}/suppliers/{sup['id']}/profile", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["kind"] == "inward"
    assert data["key_label"] == "RECEIVED"
    assert "summary" in data and "history" in data
    for k in ["total_units", "total_orders", "top_brand", "last_transaction"]:
        assert k in data["summary"]


def test_dealer_profile(bootstrap):
    d = bootstrap["dealers"][0]
    r = requests.get(f"{API}/dealers/{d['id']}/profile", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["kind"] == "outward"
    assert data["key_label"] == "DISPATCHED"


def test_supplier_profile_not_found():
    r = requests.get(f"{API}/suppliers/{uuid.uuid4()}/profile", timeout=15)
    assert r.status_code == 404


# --- Transaction edit delta math ---
def test_edit_transaction_delta_math(bootstrap):
    # Create a fresh inward, then edit qty down and verify stock deltas
    prod = next(p for p in bootstrap["products"] if p["product_type"] == "battery")
    sup = bootstrap["suppliers"][0]

    def get_row():
        rows = requests.get(f"{API}/stock", timeout=15).json()
        return next(r for r in rows if r["product_id"] == prod["id"])

    before = get_row()
    r = requests.post(f"{API}/transactions", json={
        "kind": "inward",
        "party_id": sup["id"],
        "reference": f"TEST_EDIT_{uuid.uuid4().hex[:6]}",
        "items": [{"product_id": prod["id"], "quantity": 10}],
    }, timeout=15)
    assert r.status_code == 200, r.text
    tx = r.json()
    tid = tx["transaction_id"]

    after_create = get_row()
    assert after_create["available"] == before["available"] + 10
    assert after_create["inward"] == before["inward"] + 10

    # Edit to qty 4
    r = requests.put(f"{API}/transactions/{tid}", json={
        "kind": "inward",
        "party_id": sup["id"],
        "reference": tx["reference"],
        "items": [{"product_id": prod["id"], "quantity": 4}],
    }, timeout=15)
    assert r.status_code == 200, r.text

    after_edit = get_row()
    # Net change vs before: +4
    assert after_edit["available"] == before["available"] + 4, (before, after_edit)
    assert after_edit["inward"] == before["inward"] + 4


# --- Reset endpoint (must run LAST — module-scope order) ---
def test_zzz_reset_wipes_everything():
    r = requests.post(f"{API}/admin/reset", timeout=30)
    assert r.status_code == 200
    assert r.json().get("reset") is True

    boot = requests.get(f"{API}/bootstrap", timeout=15).json()
    assert boot["brands"] == []
    assert boot["products"] == []
    assert boot["suppliers"] == []
    assert boot["dealers"] == []

    dash = requests.get(f"{API}/dashboard", timeout=15).json()
    assert dash["total_models"] == 0
    assert dash["available"] == 0
    assert dash["inward"] == 0
    assert dash["outward"] == 0

    stock = requests.get(f"{API}/stock", timeout=15).json()
    assert stock == []
