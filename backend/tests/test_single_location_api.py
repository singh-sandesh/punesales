import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


def test_single_location_and_edit_recalculates_stock():
    client = requests.Session()
    bootstrap = client.get(f"{BASE_URL}/api/bootstrap", timeout=15)
    assert bootstrap.status_code == 200
    data = bootstrap.json()
    assert "warehouses" not in data
    assert len(data["brands"]) >= 1

    brand = client.post(
        f"{BASE_URL}/api/masters/brands",
        json={"name": f"TEST_Brand_{uuid.uuid4().hex[:8]}", "code": "TST"},
        timeout=15,
    )
    assert brand.status_code == 200
    product = client.post(
        f"{BASE_URL}/api/products",
        json={"name": f"TEST_Battery_{uuid.uuid4().hex[:8]}", "brand_id": brand.json()["id"],
              "model": "TEST-M1", "capacity": "100Ah", "purchase_rate": 100},
        timeout=15,
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    before = client.get(f"{BASE_URL}/api/stock", timeout=15).json()
    assert all(row["warehouse_id"] == "main-stock" for row in before)
    assert len({row["warehouse_id"] for row in before}) == 1

    movement = client.post(
        f"{BASE_URL}/api/transactions",
        json={"kind": "inward", "reference": "TEST_EDIT", "items":[{"product_id": product_id, "quantity": 7, "rate": 100}]},
        timeout=15,
    )
    assert movement.status_code == 200
    tx = movement.json()
    row = next(x for x in client.get(f"{BASE_URL}/api/stock", timeout=15).json() if x["product_id"] == product_id)
    assert row["available"] == 7 and row["inward"] == 7

    edited = client.put(
        f"{BASE_URL}/api/transactions/{tx['transaction_id']}",
        json={"kind": "inward", "reference": "TEST_EDIT_CORRECTED", "notes": "TEST audit", "items":[{"product_id": product_id, "quantity": 4, "rate": 125}]},
        timeout=15,
    )
    assert edited.status_code == 200
    edited_data = edited.json()
    assert edited_data["total_quantity"] == 4
    assert edited_data["total_value"] == 500
    assert edited_data["edit_history"][-1]["note"] == "Posted movement corrected"
    row_after = next(x for x in client.get(f"{BASE_URL}/api/stock", timeout=15).json() if x["product_id"] == product_id)
    assert row_after["available"] == 4 and row_after["inward"] == 4


def test_invalid_and_empty_movements_rejected():
    client = requests.Session()
    empty = client.post(f"{BASE_URL}/api/transactions", json={"kind": "inward", "items": []}, timeout=15)
    assert empty.status_code == 422
    invalid = client.post(f"{BASE_URL}/api/transactions", json={"kind": "transfer", "items":[{"product_id":"missing","quantity":1,"rate":1}]}, timeout=15)
    assert invalid.status_code == 400