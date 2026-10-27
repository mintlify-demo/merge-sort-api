"""Sort API: a tiny FastAPI service that sorts numbers with quick sort.

Two endpoints:
  POST /sort        -> sorted list
  POST /sort/steps  -> sorted list plus every partition step (great for teaching)

Run it:  uvicorn main:app --reload
"""
import heapq
import time
from enum import Enum

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# The algorithm (no web code in here, so it is easy to read and test)
# --------------------------------------------------------------------------- #


def quick_sort(numbers: list[float], descending: bool = False, steps: list | None = None) -> list[float]:
    """Sort with quick sort: pick a pivot, split around it, sort each side.

    1. Pick the middle item as the pivot.
    2. Partition the rest into items that come before the pivot, items equal
       to it, and items that come after it.
    3. Quick sort the "before" and "after" groups, then join everything up.

    If a `steps` list is passed in, every partition is recorded in it.
    """
    if len(numbers) <= 1:  # base case: 0 or 1 items are already sorted
        return list(numbers)

    pivot = numbers[len(numbers) // 2]
    if descending:
        before = [n for n in numbers if n > pivot]
        after = [n for n in numbers if n < pivot]
    else:
        before = [n for n in numbers if n < pivot]
        after = [n for n in numbers if n > pivot]
    equal = [n for n in numbers if n == pivot]

    if steps is not None:
        steps.append({"step": len(steps) + 1, "pivot": pivot, "before": before, "equal": equal, "after": after})

    return quick_sort(before, descending, steps) + equal + quick_sort(after, descending, steps)


def merge_sort(numbers: list[float], descending: bool = False) -> list[float]:
    """Sort with merge sort: split in half, sort each half, merge the halves. Stable."""
    if len(numbers) <= 1:
        return list(numbers)
    middle = len(numbers) // 2
    left = merge_sort(numbers[:middle], descending)
    right = merge_sort(numbers[middle:], descending)
    merged: list[float] = []
    i = j = 0
    while i < len(left) and j < len(right):
        take_left = left[i] >= right[j] if descending else left[i] <= right[j]
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    return merged + left[i:] + right[j:]


def heap_sort(numbers: list[float], descending: bool = False) -> list[float]:
    """Sort with heap sort: build a heap, then pop the top item until it is empty."""
    heap = [-n for n in numbers] if descending else list(numbers)
    heapq.heapify(heap)
    out = [heapq.heappop(heap) for _ in range(len(heap))]
    return [-n for n in out] if descending else out


# --------------------------------------------------------------------------- #
# Request / response models (these become the OpenAPI schemas in the docs)
# --------------------------------------------------------------------------- #


class Order(str, Enum):
    asc = "asc"
    desc = "desc"


class Algorithm(str, Enum):
    quick = "quick"
    merge = "merge"
    heap = "heap"


ALGORITHMS = {"quick": quick_sort, "merge": merge_sort, "heap": heap_sort}


class SortRequest(BaseModel):
    numbers: list[float] = Field(
        ...,
        max_length=1000,
        description="The numbers to sort. Integers and decimals are both fine. Up to 1000 items.",
        examples=[[5, 2, 9, 1, 5, 6]],
    )
    order: Order = Field(
        Order.asc,
        description="Sort direction: `asc` (smallest first) or `desc` (largest first).",
        examples=["asc"],
    )
    algorithm: Algorithm = Field(
        Algorithm.quick,
        description=(
            "Which algorithm to use: `quick` (default), `merge` (stable), or `heap`. "
            "`/sort/steps` always uses `quick`."
        ),
        examples=["quick"],
    )


class SortResponse(BaseModel):
    result: list[float] = Field(..., description="The sorted numbers.", examples=[[1, 2, 5, 5, 6, 9]])
    count: int = Field(..., description="How many numbers were sorted.", examples=[6])
    order: Order = Field(..., description="The direction that was used.", examples=["asc"])
    algorithm: Algorithm = Field(..., description="The algorithm that was used.", examples=["quick"])


class PartitionStep(BaseModel):
    step: int = Field(..., description="1-based position of this partition in the run.", examples=[1])
    pivot: float = Field(..., description="The value the list was split around (the middle item).", examples=[9])
    before: list[float] = Field(..., description="Items that sort before the pivot, still unsorted.", examples=[[5, 2, 1, 5, 6]])
    equal: list[float] = Field(..., description="Items equal to the pivot.", examples=[[9]])
    after: list[float] = Field(..., description="Items that sort after the pivot, still unsorted.", examples=[[]])


class SortStepsResponse(SortResponse):
    steps: list[PartitionStep] = Field(..., description="Every partition, in the order it happened.")


class AlgorithmTiming(BaseModel):
    algorithm: Algorithm = Field(..., description="The algorithm that was timed.", examples=["quick"])
    elapsed_ms: float = Field(..., description="How long the sort took, in milliseconds.", examples=[0.042])


class SortStatsResponse(BaseModel):
    count: int = Field(..., description="How many numbers were sorted.", examples=[6])
    order: Order = Field(..., description="The direction that was used.", examples=["asc"])
    result: list[float] = Field(..., description="The sorted numbers (identical for every algorithm).", examples=[[1, 2, 5, 5, 6, 9]])
    timings: list[AlgorithmTiming] = Field(..., description="One timing per algorithm, fastest first.")
    fastest: Algorithm = Field(..., description="The algorithm that finished first on this input.", examples=["heap"])


# --------------------------------------------------------------------------- #
# The app
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="Sort API",
    version="2.0.0",
    summary="Sort numbers with quick sort and watch how it works.",
    description=(
        "A tiny demo API that sorts a list of numbers using the quick sort algorithm.\n\n"
        "Use `POST /sort` when you just want the answer, and `POST /sort/steps` when you want "
        "to see every partition along the way."
    ),
    servers=[{"url": "http://localhost:8000", "description": "Local development"}],
    openapi_tags=[
        {"name": "Sorting", "description": "Sort a list of numbers."},
    ],
)

# Allow browsers to call the API from anywhere. The docs' "Try it" playground
# sends requests straight from your browser to http://localhost:8000, so it needs CORS.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.post(
    "/sort",
    tags=["Sorting"],
    operation_id="sortNumbers",
    summary="Sort numbers",
    response_model=SortResponse,
)
def sort_numbers(body: SortRequest) -> SortResponse:
    """Sort a list of numbers in ascending or descending order.

    Pick the algorithm with `algorithm`: `quick` (default, O(n log n) on
    average), `merge` (stable, always O(n log n)), or `heap` (O(n log n),
    constant extra memory). An empty list is valid and returns an empty list.
    """
    sort = ALGORITHMS[body.algorithm.value]
    result = sort(body.numbers, descending=body.order is Order.desc)
    return SortResponse(result=result, count=len(result), order=body.order, algorithm=body.algorithm)


@app.post(
    "/sort/steps",
    tags=["Sorting"],
    operation_id="sortNumbersWithSteps",
    summary="Sort numbers and return every partition step",
    response_model=SortStepsResponse,
)
def sort_numbers_with_steps(body: SortRequest) -> SortStepsResponse:
    """Sort a list of numbers and return each partition as it happened.

    Each step shows the `pivot` and how the remaining items were split into
    `before`, `equal`, and `after` groups. Steps are listed depth-first, so the
    "before" side is fully partitioned before the "after" side starts.
    """
    steps: list = []
    result = quick_sort(body.numbers, descending=body.order is Order.desc, steps=steps)
    return SortStepsResponse(
        result=result, count=len(result), order=body.order, algorithm=Algorithm.quick, steps=steps
    )


@app.post(
    "/sort/stats",
    tags=["Sorting"],
    operation_id="compareSortAlgorithms",
    summary="Compare how long each algorithm takes",
    response_model=SortStatsResponse,
)
def compare_sort_algorithms(body: SortRequest) -> SortStatsResponse:
    """Sort the same list with every algorithm and report how long each took.

    Handy for showing that the right algorithm depends on the input. The
    `algorithm` field in the request is ignored here, since every algorithm runs.
    Timings are measured on the server and vary from run to run.
    """
    descending = body.order is Order.desc
    timings: list[AlgorithmTiming] = []
    result: list[float] = []
    for name, sort in ALGORITHMS.items():
        start = time.perf_counter()
        result = sort(body.numbers, descending=descending)
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings.append(AlgorithmTiming(algorithm=Algorithm(name), elapsed_ms=round(elapsed_ms, 4)))
    timings.sort(key=lambda t: t.elapsed_ms)
    return SortStatsResponse(
        count=len(result), order=body.order, result=result, timings=timings, fastest=timings[0].algorithm
    )
