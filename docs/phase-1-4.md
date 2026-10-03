# Phase 1–4 implementation handoff

## Implemented features

- Phase 1: email/password signup and login, PBKDF2 password hashing, short-lived access tokens, rotating revocable refresh sessions, logout, role-permission checks, audit foundation, responsive navigation shell, and local development workspace.
- Phase 2: customer profile, KYC nationality/status updates, private local KYC upload/download (PDF/PNG/JPEG up to 5 MB), operator KYC review, customer-owned current/savings/salary accounts, and a wallet with account-to-wallet deposits/withdrawals.
- Phase 3: beneficiary create/list/verify, transfer and payment posting, idempotency-key reuse detection, ownership checks, decimal amounts, transaction history, balanced debit/credit journals, and wallet posting in the same DB transaction as balance changes.
- Phase 4: masked virtual/debit/prepaid card records, card activation/freeze/unfreeze/block, daily limit API, account statements and CSV export.
- Frontend routes: `/login`, `/register`, `/dashboard`, `/accounts`, `/accounts/[id]`, `/wallet`, `/transfers`, `/payments`, `/cards`, `/statements`, `/profile`, and `/security`.
- Web base UI: Tailwind CSS 4 setup, shadcn/ui component configuration, shared Button primitive, Lucide icons, React Query and exact workspace install commands.

## Files and module boundaries

- `apps/web/src/app`: Next.js routes and theme stylesheet.
- `apps/web/src/components`: authenticated shell, query provider, reusable phase screens.
- `apps/web/src/components/screen-primitives.tsx`, `screen-actions.tsx`, `screen-statements.tsx`: shared UI, forms/actions and statement/account detail screens.
- `apps/web/src/components/ui/button.tsx`: small source-owned shadcn/ui button primitive.
- `apps/web/src/lib`: API client, refresh handling and statement download.
- `apps/api/app/core`: settings, database sessions and JWT/password helpers.
- `apps/api/app/modules`: identity, customers/KYC, accounts/wallet, payments/ledger and cards.
- `apps/api/migrations`: Alembic schema revisions.
- `apps/api/tests`: API tests with an isolated SQLite database.
- `.vscode`: recommended extensions, launch config, settings and terminal tasks.

## APIs added

- `/api/v1/auth`: register, login, refresh and logout; `/auth/me`.
- `/api/v1/customers`: own profile/KYC, private document upload/list/download, permission-guarded customer listing and KYC review.
- `/api/v1/accounts`, `/api/v1/wallet`, `/api/v1/beneficiaries`.
- `/api/v1/transfers`, `/api/v1/payments`, `/api/v1/transactions`, statement JSON/CSV and transaction journal details.
- `/api/v1/cards`: issue/list, activate/freeze/unfreeze/block and daily limit update.
- OpenAPI docs: `/docs`.

## Database changes

- Revision `0001_phase_1_4`: users, customers, KYC docs, role permissions, audit logs, accounts, wallets, beneficiaries, transactions, ledger accounts, journal entries/lines and cards.
- Revision `0002_refresh_sessions`: persisted revocable refresh sessions.
- Money fields use `NUMERIC(20,4)`; financial amounts are represented as `Decimal` in Python.

## Tests and checks

- API tests cover registration/login, resource ownership, refresh rotation/revocation, duplicate and mismatched idempotency requests, balanced ledger entries, wallet ledger posting, card transitions and role permission enforcement.
- Run `cd apps/api && pytest -q` and `ruff check .`.
- Run `corepack pnpm typecheck:web`, `corepack pnpm lint:web`, and `corepack pnpm build:web` from the repository root.

## Local commands

```bash
corepack prepare pnpm@10.15.1 --activate
corepack pnpm install
corepack pnpm add --filter @finsphere/web tailwindcss @tailwindcss/postcss postcss class-variance-authority tailwind-merge
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e 'apps/api[dev]'
cp .env.example .env
cd apps/api
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

In another terminal at the repository root: `corepack pnpm dev:web`.

## Known remaining items

- Identity verification, face check, OTP delivery and MFA are not integrated; KYC review is an operations decision over uploaded records.
- Payments/transfers are internal simulations; no bank, IBFT, card network, FX, remittance, external biller or settlement provider is connected.
- Card numbers are not issued by a network; only generated last-four display data is stored. PIN, ATM/POS controls and real card transactions are not included.
- Local KYC file storage must move to private object storage before shared deployment. Browser bearer-token storage needs a hardened session design before production.
- Statement export is CSV only; PDF/XLSX generation, date filtering and scheduled delivery remain future work.
- Rate limiting, lockout policy, TOTP setup, trusted devices, ABAC/tenant isolation and broader authorization policy management are not included in this phase slice.
- For production, replace local credentials and JWT secret, add real monitoring, security review, external-provider controls and operational runbooks.

## Next phase

Phase 5 adds lending, explicitly simulated credit decision support, BNPL and collections. Before starting it, keep migrations additive and preserve the transaction/ledger API contracts from Phase 3.
