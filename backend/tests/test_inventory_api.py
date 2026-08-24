import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


@pytest.fixture(scope="module")
def client():
    with requests.Session() as session:
        session.headers.update({"Content-Type": "application/json"})
        yield session


@pytest.fixture(scope="module")
def bootstrap(client):
    response = client.get(f"{BASE_URL}/api/bootstrap", timeout=15)
    assert response.status_code == 200
    return response.json()


def test_bootstrap_has_seeded_inventory_masters(client, bootstrap):
    assert len(bootstrap["brands"]) >= 3
    assert len(bootstrap["products"]) >= 9
    assert len(bootstrap["warehouses"]) >= 1
    stock = client.get(f"{BASE_URL}/api/stock", timeout=15)
    assert stock.status_code == 200
    assert len(stock.json()) >= 9
    assert all("_id" not in row for row in stock.json())


def test_dashboard_has_nonzero_seeded_kpis(client):
    response = client.get(f"{BASE_URL}/api/dashboard", timeout=15)
    assert response.status_code == 200
    data = response.json()
    assert data["available"] > 0
    assert data["inward"] > 0
    assert data["outward"] > 0
    assert data["inventory_value"] > 0


def test_post_inward_persists_and_updates_stock(client, bootstrap):
    product = bootstrap["products"][0]
    warehouse = bootstrap["warehouses"][0]
    before = client.get(f"{BASE_URL}/api/stock", timeout=15).json()
    row = next(x for x in before if x["product_id"] == product["id"] and x["warehouse_id"] == warehouse["id"])
    quantity = 2
    response = client.post(f"{BASE_URL}/api/transactions", json={
        "kind": "inward", "warehouse_id": warehouse["id"], "reference": f"TEST_{uuid.uuid4().hex}",
        "items": [{"product_id": product["id"], "quantity": quantity, "rate": 1}],
    }, timeout=15)
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["transaction_id"].startswith("INW-")
    assert transaction["total_quantity"] == quantity
    ledger = client.get(f"{BASE_URL}/api/ledger", timeout=15).json()
    assert any(x["id"] == transaction["id"] and x["total_quantity"] == quantity for x in ledger)
    after = client.get(f"{BASE_URL}/api/stock", timeout=15).json()
    updated = next(x for x in after if x["id"] == row["id"])
    assert updated["available"] == row["available"] + quantity


def test_outward_rejects_quantity_above_available(client, bootstrap):
    product = bootstrap["products"][0]
    warehouse = bootstrap["warehouses"][0]
    row = next(x for x in client.get(f"{BASE_URL}/api/stock", timeout=15).json()
               if x["product_id"] == product["id"] and x["warehouse_id"] == warehouse["id"])
    response = client.post(f"{BASE_URL}/api/transactions", json={
        "kind": "outward", "warehouse_id": warehouse["id"], "items": [
            {"product_id": product["id"], "quantity": row["available"] + 1, "rate": 1}
        ],
    }, timeout=15)
    assert response.status_code == 400
    assert "Not enough available stock" in response.json()["detail"]