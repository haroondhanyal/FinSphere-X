<p align="center">
  <a href="https://github.com/haroondhanyal/FinSphere-X">
    <img src="https://raw.githubusercontent.com/haroondhanyal/FinSphere-X/main/assets/finsphere-x-logo.svg" alt="FinSphere X — Banking Beyond Borders" width="520" />
  </a>
</p>

<h1 align="center">FinSphere X</h1>
<p align="center"><strong>AI-Powered Digital Banking &amp; Financial Operations Platform</strong></p>
<p align="center"><a href="https://github.com/haroondhanyal/FinSphere-X">GitHub Repository</a> · Banking Beyond Borders</p>

## Phase 1–4 release

This release establishes authentication and role permissions, the customer profile and KYC flow, account and wallet operations, beneficiary transfers and payments with double-entry journal records, card controls, and account statements. Read [the complete product roadmap](docs/roadmap.md) for screens and all 14 planned phases.

| Phase | Status      | Delivered in this release                                                                                                          |
| ----- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Implemented | pnpm workspace, FastAPI API, PostgreSQL/SQLite development DB, JWT authentication, role permissions, responsive app shell          |
| 2     | Implemented | Customer profile, KYC details and document upload/review, multi-account support, wallet balances and account-wallet moves          |
| 3     | Implemented | Beneficiaries and verification, transfers and payments, idempotency keys, immutable transaction references, balanced journal lines |
| 4     | Implemented | Masked virtual card issuance, activate/freeze/unfreeze/block controls, account statement JSON and CSV export                       |
| 5–14  | Planned     | Loans, business and merchant services, finance operations, risk, AI, open banking and cloud platform work                          |

## Run locally

Requirements: Node.js 22+, Corepack, Python 3.11+, and PostgreSQL (or SQLite for quick local work).

### Install

```bash
corepack prepare pnpm@10.15.1 --activate
corepack pnpm install
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e 'apps/api[dev]'
cp .env.example .env
```

Replace the example `JWT_SECRET` in `.env` with a private random value before starting a shared environment.

### Start the API

From the VS Code terminal, in the repository root:

```bash
cd apps/api
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs). For PostgreSQL set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/DATABASE`; SQLite is the default for a quick start.

### Start the web app

In a second VS Code terminal at the repository root:

```bash
corepack pnpm dev:web
```

Open [http://localhost:3000](http://localhost:3000). Set `NEXT_PUBLIC_API_URL` if the API is hosted elsewhere.

### Demo accounts

After `python -m app.seed`, use `customer@finspherex.com`, `operations@finspherex.com`, or `admin@finspherex.com`. The local demo password is `FinSphere-Demo-2026!`. These seed credentials are for disposable local data only; change or remove them before any shared deployment.

### Docker Compose

```bash
docker compose up --build
```

This starts the web app, API, and PostgreSQL with local-only credentials. Do not expose this configuration to a public network.

## Verify Phase 1–4

```bash
cd apps/api && pytest
cd ../..
corepack pnpm typecheck:web
corepack pnpm lint:web
corepack pnpm build:web
```

## Architecture

- `apps/web`: Next.js app routes, shared dashboard shell, responsive feature screens and typed API helper.
- `apps/api`: FastAPI routers, Pydantic DTOs, SQLAlchemy models, migration and service layer.
- `apps/web/src/components`: small reusable screen primitives, form controls, statements, and the shadcn-style UI button.
- `docs`: product roadmap, screen inventory and architecture.
- `assets`: FinSphere X logo asset used in this README.

Start with [architecture and code conventions](docs/architecture.md). The initial implementation is a modular monolith: feature folders keep responsibilities clear without requiring developers to operate many services at once.

The web base uses Tailwind CSS 4, a source-owned shadcn/ui Button primitive, and Lucide icons. Install the UI dependencies with `corepack pnpm add --filter @finsphere/web tailwindcss @tailwindcss/postcss postcss class-variance-authority tailwind-merge`.

## Financial and security boundaries

- Money is parsed with Python `Decimal` and persisted as PostgreSQL `NUMERIC(20,4)`.
- Transfer and wallet move endpoints require idempotency keys and write a balanced debit/credit journal in the same database transaction as account balance changes.
- Users can access only their own customer, account, wallet, beneficiary, card, transaction, and statement records. Operations endpoints use seeded role permissions.
- Card data stores only a generated last-four display value; no PAN or CVV is accepted or stored.
- KYC uploads are size/type limited and stored under a private local directory in this development phase.
- External payments, identity checks, OTP, MFA, and card network processing are not connected. This release is a functional development prototype, not a regulated banking service.
