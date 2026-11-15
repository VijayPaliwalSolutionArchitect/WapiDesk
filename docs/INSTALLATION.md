# WapiDesk — Installation

## Prerequisites

- Python 3.10+ (developed on 3.14)
- pip
- Git

## Steps

```bash
git clone https://github.com/VijayPaliwalSolutionArchitect/WapiDesk.git
cd WapiDesk/backend
python -m venv .venv
source .venv/Scripts/activate        # Windows git-bash / .venv\Scripts\activate on cmd
pip install -r requirements.txt
```

## Verify

```bash
python -c "import fastapi, pydantic_settings; print('deps ok')"
```

## First boot

```bash
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs  (OpenAPI)
# http://127.0.0.1:8000/api/health
```

The backend auto-creates `data/wapidesk.db` (SQLite) and seeds the knowledge
base, orders, services, and memory on first boot.

## Tests

```bash
python -m pytest            # runs against :memory:
```
