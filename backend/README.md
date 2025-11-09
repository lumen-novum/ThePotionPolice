# Backend (Flask)

This is a minimal Flask backend used for local development. It exposes a few example API endpoints used by the frontend:

- `GET /api/cauldrons` — returns an array of cauldrons with `id`, `name`, `lat`, `lng`, and `levels` (time-series sample data).
- `GET /api/network-map` — returns an array of paths with `coordinates` arrays for the map.
- `GET /api/tickets` — returns a small sample list of tickets.

Run locally (macOS / zsh):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

This starts the Flask dev server on `http://127.0.0.1:5000`.

You can also use `flask run` if you prefer to set `FLASK_APP=app.py`.
