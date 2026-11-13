# Podotchet Core — notes for contributors and AI assistants

Public showcase extracted from a production expense-tracking SaaS. Clean history,
fictional demo data only (Acme Trading LLC, USD).

- Backend: `backend/app` — FastAPI + SQLAlchemy 2.0, Alembic in `backend/alembic`.
  Run tests: `cd backend && pytest -q` (SQLite by default; set `DATABASE_URL` for Postgres).
- Frontend: `frontend/src` — React 18 + TypeScript, React Query, lucide-react, en/ru i18n.
- Every query is scoped by `org_id`; load single rows with `core.deps.get_in_org` (404 across tenants).
- Permissions live in `core/rbac.py` (matrix); approval lifecycle in `services/approval.py`.
- Never hard-delete financial rows: `services/soft_delete.soft_delete` + `services/audit.log_delete`.
- Keep files under 300 lines. No secrets in the repo; `.env` is git-ignored.
