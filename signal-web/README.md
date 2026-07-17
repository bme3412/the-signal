# signal-web

React + Vite + Tailwind v4 frontend for The Signal. Full project docs, feature
overview, and architecture live in the [root README](../README.md).

## Develop

```bash
npm install
npm run dev      # http://localhost:5173, proxies /api and /data to :8000
```

Requires the backend running on port 8000 (see root README). No `.env` is
needed for local development — the Vite proxy handles routing.

## Deploy (Vercel)

`vercel.json` is configured; set `VITE_API_URL` in the Vercel dashboard to
your publicly hosted backend URL.
