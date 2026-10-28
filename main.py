"""Merge Sort API: a tiny FastAPI service that sorts numbers with merge sort.

Two endpoints:
  POST /sort        -> sorted list
  POST /sort/steps  -> sorted list plus every merge step (great for teaching)

Run it:  uvicorn main:app --reload
"""
from enum import Enum

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# The algorithm (no web code in here, so it is easy to read and test)
# --------------------------------------------------------------------------- #


def merge(left: list[float], right: list[float], descending: bool = False) -> list[float]:
    """Merge two already-sorted lists into one sorted list."""
    merged: list[float] = []
    i = j = 0
    while i < len(left) and j < len(right):
        # Take from the left list when it should come first. Using <= (or >=)
        # keeps the sort stable: equal values stay in their original order.
        take_left = left[i] >= right[j] if descending else left[i] <= right[j]
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    # One side ran out, so whatever is left on the other side is already sorted.
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def merge_sort(numbers: list[float], descending: bool = False, steps: list | None = None) -> list[float]:
    """Sort with merge sort: split in half, sort each half, merge the halves.

    If a `steps` list is passed in, every merge is recorded in it.
    """
    if len(numbers) <= 1:  # base case: 0 or 1 items are already sorted
        return list(numbers)

    middle = len(numbers) // 2
    left = merge_sort(numbers[:middle], descending, steps)
    right = merge_sort(numbers[middle:], descending, steps)
    merged = merge(left, right, descending)

    if steps is not None:
        steps.append({"step": len(steps) + 1, "left": left, "right": right, "merged": merged})
    return merged


# --------------------------------------------------------------------------- #
# Request / response models (these become the OpenAPI schemas in the docs)
# --------------------------------------------------------------------------- #


class Order(str, Enum):
    asc = "asc"
    desc = "desc"


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


class SortResponse(BaseModel):
    result: list[float] = Field(..., description="The sorted numbers.", examples=[[1, 2, 5, 5, 6, 9]])
    count: int = Field(..., description="How many numbers were sorted.", examples=[6])
    order: Order = Field(..., description="The direction that was used.", examples=["asc"])


class MergeStep(BaseModel):
    step: int = Field(..., description="1-based position of this merge in the run.", examples=[1])
    left: list[float] = Field(..., description="The sorted left half going into the merge.", examples=[[5]])
    right: list[float] = Field(..., description="The sorted right half going into the merge.", examples=[[2]])
    merged: list[float] = Field(..., description="The result of merging left and right.", examples=[[2, 5]])


class SortStepsResponse(SortResponse):
    steps: list[MergeStep] = Field(..., description="Every merge, in the order it happened.")


# --------------------------------------------------------------------------- #
# The app
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="Merge Sort API",
    version="1.0.0",
    summary="Sort numbers with merge sort and watch how it works.",
    description=(
        "A tiny demo API that sorts a list of numbers using the merge sort algorithm.\n\n"
        "Use `POST /sort` when you just want the answer, and `POST /sort/steps` when you want "
        "to see every merge along the way."
    ),
    servers=[{"url": "http://localhost:8000", "description": "Local development"}],
    openapi_tags=[
        {"name": "Sorting", "description": "Sort a list of numbers."},
    ],
)

# Allow browsers to call the API from anywhere. The docs' "Try it" playground
# sends requests straight from your browser to the API, so it needs CORS.
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

    The sort is **stable** and runs in O(n log n) time. An empty list is valid
    and returns an empty list.
    """
    result = merge_sort(body.numbers, descending=body.order is Order.desc)
    return SortResponse(result=result, count=len(result), order=body.order)


@app.post(
    "/sort/steps",
    tags=["Sorting"],
    operation_id="sortNumbersWithSteps",
    summary="Sort numbers and return every merge step",
    response_model=SortStepsResponse,
)
def sort_numbers_with_steps(body: SortRequest) -> SortStepsResponse:
    """Sort a list of numbers and return each merge as it happened.

    Each step shows the two sorted halves (`left` and `right`) and the list they
    were merged into. The last step's `merged` list is the final result.
    """
    steps: list = []
    result = merge_sort(body.numbers, descending=body.order is Order.desc, steps=steps)
    return SortStepsResponse(result=result, count=len(result), order=body.order, steps=steps)
