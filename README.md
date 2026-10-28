# Merge Sort API

A tiny [FastAPI](https://fastapi.tiangolo.com/) service that sorts numbers with merge sort. Part of the [Mintlify demo org](https://github.com/mintlify-demo). Docs: [https://mintlify-demo.mintlify.site/merge-sort-api](https://mintlify-demo.mintlify.site/merge-sort-api).

| Endpoint | What it does |
| --- | --- |
| `POST /sort` | Sort a list of numbers (`order`: `asc` or `desc`) |
| `POST /sort/steps` | Same, and also returns every merge step |

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload        # http://localhost:8000  (Swagger UI at /docs)
```

```bash
curl -X POST localhost:8000/sort -H 'Content-Type: application/json' \
  -d '{"numbers": [5, 2, 9, 1], "order": "asc"}'
```

## Test it

```bash
python -m pytest -q
```

## Docs

Published at [https://mintlify-demo.mintlify.site/merge-sort-api](https://mintlify-demo.mintlify.site/merge-sort-api) (sign-in required). The pages and the API spec live in the [`docs` repo, under `merge-sort-api/`](https://github.com/mintlify-demo/docs/tree/main/merge-sort-api), not here. This repo holds only code and tests. When a pull request here changes the API, Mintlify's *Update from code changes* automation opens a pull request in the `docs` repo with the matching docs update.

## Hosting

TODO(hosting): the API will be hosted with Mintlify's internal tooling (details TBD). Until then the OpenAPI `servers` list only `http://localhost:8000`. When the hosted URL exists, add it as the first entry of `servers=[...]` in `main.py`, update the `servers` list in the `docs` repo's spec too, and rebase the demo stack (see the demo kit README).

`docs` repo `merge-sort-api/guides/sorting-at-scale.mdx` is gated to the `enterprise` group with `groups` frontmatter.

## Ticket → file map

Context for Mintlify's *Update docs from tickets* automation (seed tickets: `linear-tickets.json` in the demo kit).

| Ticket | What | Where |
| --- | --- | --- |
| DEMO-1 | Reject lists over 10,000 numbers with `413` | `main.py` (`SortRequest`, `sort_numbers`), `docs` repo `merge-sort-api/guides/sorting-at-scale.mdx` |
