# Frontend: API proxy & environment configuration

This project uses Vite for development. You can point frontend API calls to a separate Flask backend in two ways:

1) Dev proxy (recommended for local development)

- Vite will forward any request starting with `/api` to the proxy target configured in `vite.config.js`.
- By default this project proxies `/api` to `http://localhost:5000` (edit `frontend/vite.config.js` to change the port/host).

Usage:

```bash
cd "frontend"
npm run dev
```

Keep your Flask backend running (for example `FLASK_RUN_PORT=5000 flask run`) and the Vite dev server will transparently forward `/api/*` requests so your client code can keep using relative paths like `fetch('/api/cauldrons')`.

2) Explicit API host via environment variable (recommended for preview or production builds)

- Set `VITE_API_URL` to the full base URL of your API (e.g. `http://localhost:5000` or `https://api.example.com`). The frontend code will call `${VITE_API_URL}/api/...` when this is set.

Create a `.env` or `.env.development` in `frontend/` with:

```
VITE_API_URL=http://localhost:5000
```

Then restart the dev server. This is useful for previewing a production build against a running API or when your frontend and backend are on different origins.

Notes & tips
- The Vite proxy only runs in development. For production, use `VITE_API_URL` or host frontend and backend under the same origin to avoid CORS.
- To change the proxy target, edit `vite.config.js` and set the `server.proxy['/api'].target` value to your Flask URL.
- Example: change `target` to `http://localhost:5001` if your Flask server uses port 5001.
