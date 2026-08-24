import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


def test_quick_master_creation_and_multi_item_transaction_persist():
    """Regression coverage for dynamic masters and multi-line movements."""
    client = requests.Session()
    suffix = uuid.uuid4().hex[:8]
    bootstrap = client.get(f"{BASE_URL}/api/bootstrap", timeout=15).json()
    stock = client.get(f"{BASE_URL}/api/stock", timeout=15).json()
    warehouse_id = stock[0]["warehouse_id"]
    stock_rows = [row for row in stock if row["warehouse_id"] == warehouse_id and row["available"] >= 2]
    warehouse = next(item for item in bootstrap["warehouses"] if item["id"] == warehouse_id)
    products = [next(item for item in bootstrap["products"] if item["id"] == row["product_id"]) for row in stock_rows[:2]]

    dealer = client.post(
        f"{BASE_URL}/api/masters/dealers",
        json={"name": f"TEST_Dealer_{suffix}", "details": {"opening_balance": 1250}},
        timeout=15,
    )
    assert dealer.status_code == 200
    dealer_data = dealer.json()
    assert dealer_data["name"].startswith("TEST_Dealer_")
    assert dealer_data["opening_balance"] == 1250

    transaction = client.post(
        f"{BASE_URL}/api/transactions",
        json={
            "kind": "outward",
            "party_id": dealer_data["id"],
            "warehouse_id": warehouse["id"],
            "reference": f"TEST_{suffix}",
            "items": [
                {"product_id": products[0]["id"], "quantity": 1, "rate": 10},
                {"product_id": products[1]["id"], "quantity": 2, "rate": 20},
            ],
        },
        timeout=15,
    )
    assert transaction.status_code == 200
    assert transaction.json()["total_quantity"] == 3

    profile = client.get(f"{BASE_URL}/api/dealers/{dealer_data['id']}/profile", timeout=15)
    assert profile.status_code == 200
    profile_data = profile.json()
    assert profile_data["summary"]["total_units"] == 3
    assert profile_data["summary"]["total_value"] == 50
    assert profile_data["summary"]["outstanding"] == 1300
    assert len(profile_data["history"]) == 2


def test_empty_transaction_is_rejected():
    """A posted movement must contain at least one positive line item."""
    bootstrap = requests.get(f"{BASE_URL}/api/bootstrap", timeout=15).json()
    response = requests.post(
        f"{BASE_URL}/api/transactions",
        json={"kind": "inward", "warehouse_id": bootstrap["warehouses"][0]["id"], "items": []},
        timeout=15,
    )
    assert response.status_code == 400