from fastapi.testclient import TestClient

import pytest

from main import app, heap_sort, merge_sort, quick_sort

client = TestClient(app)


def test_quick_sort_function():
    assert quick_sort([5, 2, 9, 1]) == [1, 2, 5, 9]
    assert quick_sort([5, 2, 9, 1], descending=True) == [9, 5, 2, 1]
    assert quick_sort([3, 1, 3, 2, 3]) == [1, 2, 3, 3, 3]
    assert quick_sort([]) == []
    assert quick_sort([7]) == [7]


def test_sort_ascending_by_default():
    r = client.post("/sort", json={"numbers": [5, 2, 9, 1, 5, 6]})
    assert r.status_code == 200
    assert r.json() == {"result": [1, 2, 5, 5, 6, 9], "count": 6, "order": "asc", "algorithm": "quick"}


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


def test_steps_show_each_partition():
    r = client.post("/sort/steps", json={"numbers": [4, 3, 2, 1]})
    body = r.json()
    assert body["result"] == [1, 2, 3, 4]
    first = body["steps"][0]
    assert first == {"step": 1, "pivot": 2, "before": [1], "equal": [2], "after": [4, 3]}
    assert [s["pivot"] for s in body["steps"]] == [2, 3]
    assert [s["step"] for s in body["steps"]] == [1, 2]


def test_steps_for_single_item_is_empty():
    r = client.post("/sort/steps", json={"numbers": [1]})
    assert r.json()["steps"] == []


@pytest.mark.parametrize("fn", [quick_sort, merge_sort, heap_sort])
def test_every_algorithm_sorts(fn):
    assert fn([5, 2, 9, 1, 5]) == [1, 2, 5, 5, 9]
    assert fn([5, 2, 9, 1, 5], descending=True) == [9, 5, 5, 2, 1]
    assert fn([]) == []


@pytest.mark.parametrize("algorithm", ["quick", "merge", "heap"])
def test_sort_with_algorithm(algorithm):
    r = client.post("/sort", json={"numbers": [3, 1, 2], "algorithm": algorithm})
    assert r.status_code == 200
    assert r.json()["result"] == [1, 2, 3]
    assert r.json()["algorithm"] == algorithm


def test_unknown_algorithm_is_rejected():
    r = client.post("/sort", json={"numbers": [1], "algorithm": "bogo"})
    assert r.status_code == 422


def test_stats_compares_every_algorithm():
    r = client.post("/sort/stats", json={"numbers": [5, 2, 9, 1, 5, 6], "order": "desc"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == [9, 6, 5, 5, 2, 1]
    assert body["count"] == 6
    assert sorted(t["algorithm"] for t in body["timings"]) == ["heap", "merge", "quick"]
    elapsed = [t["elapsed_ms"] for t in body["timings"]]
    assert elapsed == sorted(elapsed)
    assert body["fastest"] == body["timings"][0]["algorithm"]
