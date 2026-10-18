# FastAPI and SQLite backend, React frontend

Python is the ecosystem for the AI work, so the backend is FastAPI on SQLite (one file, easy to back up, enough for one user), with sqlite-vec for embeddings. The UI is a separate React + TypeScript app, which handles editable tables, an approval inbox and dashboards far better than Python UI frameworks and makes a more credible open-source project.

## Considered Options

- Streamlit or NiceGUI: faster to start, painful for CRUD tables and approval flows.
- Postgres: unnecessary operational weight for a single-user local app.
