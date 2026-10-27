# Merge Sort API

A tiny [FastAPI](https://fastapi.tiangolo.com/) service that sorts numbers with merge sort. Part of the [Mintlify demo org](https://github.com/mintlify-demo): the `docs/` folder holds this API's Mintlify docs.

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

## Regenerate the OpenAPI spec

`docs/openapi.json` is committed so Mintlify can build the API reference without running the app. After changing `main.py`:

```bash
python scripts/export_openapi.py    # or: make spec
```

A test fails if the committed spec is out of date.

## Docs

`docs/` is a complete Mintlify project (`docs.json`, MDX pages, `openapi.json`). The central [`docs`](https://github.com/mintlify-demo/docs) repo publishes it at `/merge-sort-api`. Preview just this folder with `cd docs && mint dev`.
