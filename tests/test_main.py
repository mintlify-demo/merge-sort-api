from fastapi.testclient import TestClient

from main import app, merge_sort

client = TestClient(app)


def test_merge_sort_function():
    assert merge_sort([5, 2, 9, 1]) == [1, 2, 5, 9]
    assert merge_sort([5, 2, 9, 1], descending=True) == [9, 5, 2, 1]
    assert merge_sort([]) == []
    assert merge_sort([7]) == [7]


def test_sort_ascending_by_default():
    r = client.post("/sort", json={"numbers": [5, 2, 9, 1, 5, 6]})
    assert r.status_code == 200
    assert r.json() == {"result": [1, 2, 5, 5, 6, 9], "count": 6, "order": "asc"}


def test_sort_descending():
    r = client.post("/sort", json={"numbers": [3, 1, 2], "order": "desc"})
    assert r.json()["result"] == [3, 2, 1]


def test_sort_handles_decimals_and_negatives():
    r = client.post("/sort", json={"numbers": [0.5, -2, 3.25, -2]})
    assert r.json()["result"] == [-2, -2, 0.5, 3.25]


def test_sort_empty_list():
    r = client.post("/sort", json={"numbers": []})
    assert r.status_code == 200
    assert r.json()["result"] == []


def test_invalid_order_is_rejected():
    r = client.post("/sort", json={"numbers": [1], "order": "sideways"})
    assert r.status_code == 422


def test_non_numbers_are_rejected():
    r = client.post("/sort", json={"numbers": ["a", "b"]})
    assert r.status_code == 422


def test_steps_show_each_merge():
    r = client.post("/sort/steps", json={"numbers": [4, 3, 2, 1]})
    body = r.json()
    assert body["result"] == [1, 2, 3, 4]
    assert [s["merged"] for s in body["steps"]] == [[3, 4], [1, 2], [1, 2, 3, 4]]
    assert [s["step"] for s in body["steps"]] == [1, 2, 3]


def test_steps_for_single_item_is_empty():
    r = client.post("/sort/steps", json={"numbers": [1]})
    assert r.json()["steps"] == []
