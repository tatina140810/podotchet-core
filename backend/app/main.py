from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.services.soft_delete  # noqa: F401  registers the global soft-delete filter
from app.config import get_settings
from app.routers import approvals, auth, directory, expenses, reports

app = FastAPI(title="Podotchet Core", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, expenses, approvals, reports, directory):
    app.include_router(r.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
