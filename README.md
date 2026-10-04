<p align="center">
  <a href="https://github.com/haroondhanyal/FinSphere-X">
    <img src="https://raw.githubusercontent.com/haroondhanyal/FinSphere-X/main/assets/finsphere-x-logo.svg" alt="FinSphere X — Banking Beyond Borders" width="520" />
  </a>
</p>

<h1 align="center">FinSphere X</h1>
<p align="center"><strong>AI-Powered Digital Banking &amp; Financial Operations Platform</strong></p>
<p align="center"><a href="https://github.com/haroondhanyal/FinSphere-X">GitHub Repository</a> · Banking Beyond Borders</p>

## Phases 1–14 implementation status

The repository now contains implementation slices for all 14 roadmap phases. Customer workspace screens include onboarding, support, activity, budgeting, savings goals, and simulated term deposits. Phases 9–14 add local simulations, browser tests and deployment templates; real financial providers, production AI and provisioned cloud infrastructure are not included. See the [Phase 5–8 guide](docs/phase-5-8.md), [Phase 9–14 guide](docs/phase-9-14.md), and [complete product roadmap](docs/roadmap.md) for scope and limits.

| Phase | Status      | Delivered in this release                                                                                                          |
| ----- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Implemented | pnpm workspace, FastAPI API, PostgreSQL/SQLite development DB, JWT authentication, TOTP MFA with one-time recovery codes, role permissions, revocable sessions, responsive app shell |
| 2     | Implemented | Customer profile, KYC details and document upload/review, multi-account support, wallet balances and account-wallet moves          |
| 3     | Implemented | Beneficiaries and verification, transfers and payments, idempotency keys, immutable transaction references, balanced journal lines |
| 4     | Implemented | Masked virtual card issuance, activate/freeze/unfreeze/block controls, account statement JSON and CSV export                       |
| 5     | Implemented | Loan products and request-shape score, application decisions, illustrative repayment schedule, BNPL and demo collections            |
| 6     | Implemented | Business dashboard, invoices/expenses/payroll approvals, merchant sales/refunds/disputes and settlement review                      |
| 7     | Implemented | Journal detail and trial balance, manual reconciliation, configurable fees and settlement fee application                           |
| 8     | Implemented | Fraud/AML/sanctions cases, synthetic screening fixture, notes/evidence, human decisions and audit records                            |
| 9     | Sandbox     | Investment catalog/portfolio, treasury liquidity view, static FX quotes and reviewed remittance requests                            |
| 10    | Implemented | Optional OpenAI-backed explanations, summaries and pasted-text/PDF/image extraction; application-calculated historical averages |
| 11    | Sandbox     | Fictional open-banking consent, hashed read-only API keys and queued webhook test records                                              |
| 12    | Implemented | API tests, Playwright login checks, CI, source secret scan and k6 smoke scenario                                                      |
| 13    | Template    | Non-root Docker images, Compose readiness, request IDs, Prometheus metrics and GitHub Actions                                        |
| 14    | Template    | Kustomize Kubernetes workloads and Terraform AWS network/RDS baseline; not provisioned                                               |

## Application screenshots

Screenshots of the current FinSphere X interface are collected below. The review queues and operations views use fictional demo data.

| Dashboard | Loans review | Collections |
| --- | --- | --- |
| <img src="docs/screenshots/dashboard.jpg" alt="Dashboard" width="320" /> | <img src="docs/screenshots/loans-review.jpg" alt="Loans review" width="320" /> | <img src="docs/screenshots/collections.jpg" alt="Collections" width="320" /> |

| KYC review | Business review | Payroll review |
| --- | --- | --- |
| <img src="docs/screenshots/kyc-review.jpg" alt="KYC review" width="320" /> | <img src="docs/screenshots/business-review.jpg" alt="Business review" width="320" /> | <img src="docs/screenshots/payroll-review.jpg" alt="Payroll review" width="320" /> |

| Settlement review | Expense review | Merchant disputes |
| --- | --- | --- |
| <img src="docs/screenshots/settlement-review.jpg" alt="Settlement review" width="320" /> | <img src="docs/screenshots/expense-review.jpg" alt="Expense review" width="320" /> | <img src="docs/screenshots/merchant-disputes.jpg" alt="Merchant disputes" width="320" /> |

| Finance ledger | Risk casework | Treasury liquidity |
| --- | --- | --- |
| <img src="docs/screenshots/finance-ledger.jpg" alt="Finance ledger" width="320" /> | <img src="docs/screenshots/risk-casework.jpg" alt="Risk casework" width="320" /> | <img src="docs/screenshots/treasury-liquidity.jpg" alt="Treasury liquidity" width="320" /> |

| Remittance review | Developer platform | Members and accounts |
| --- | --- | --- |
| <img src="docs/screenshots/remittance-review.jpg" alt="Remittance review" width="320" /> | <img src="docs/screenshots/developer-platform.jpg" alt="Developer platform" width="320" /> | <img src="docs/screenshots/members-accounts.jpg" alt="Members and accounts" width="320" /> |

| Mobile login |
| --- |
| <img src="docs/screenshots/login-mobile.jpg" alt="FinSphere X mobile login" width="240" /> |

## Advanced application flow

The screenshots above are current captures from the running FinSphere X interface. They cover customer operations, review queues, finance/risk work, treasury, remittance, and the developer sandbox. Each image is stored in `docs/screenshots/` so it renders in the repository and in this README.

```mermaid
flowchart LR
  subgraph Customer[Customer workspace]
    Signup[Register and sign in] --> Setup[Profile and KYC submission]
    Setup --> Accounts[Accounts, wallet and cards]
    Accounts --> Activity[Transfers and payments]
    Activity --> Ledger[Atomic balance and ledger posting]
    Accounts --> Plans[Budgets, goals and deposit projections]
    Accounts --> Help[Support and activity feed]
  end

  subgraph Business[Business and merchant workspace]
    Org[Organization onboarding] --> Invoice[Invoices and expenses]
    Invoice --> Payroll[Payroll preparation]
    Payroll --> StaffReview[Human approvals]
    Org --> Sales[Merchant sales and disputes]
  end

  subgraph Operations[Operations and administration]
    KycReview[KYC review] --> Risk[Risk and compliance casework]
    Credit[Loan and collections review] --> Finance[Finance and reconciliation]
    StaffReview --> Settlement[Settlement review]
    Finance --> Audit[Audit trail]
    Risk --> Audit
  end

  subgraph Platform[Shared platform]
    Web[Next.js role-aware UI] --> API[FastAPI auth, validation and ownership checks]
    API --> DB[(PostgreSQL or local SQLite)]
    API --> Audit
    Copilot[Consent-based AI assistance] -. optional provider .-> OpenAI[OpenAI API]
    Dev[Read-only sandbox API keys] --> API
  end

  Customer --> Web
  Business --> Web
  Operations --> Web
  Web --> API
  API --> DB
  Activity --> API
  Plans --> API
  Help --> API
  Invoice --> API
  Sales --> API
  Copilot --> API
```

### End-to-end examples

1. **Customer onboarding:** register → complete profile → submit KYC details/documents → operations reviews and records a decision → customer sees the updated status.
2. **Customer payment:** select an owned account and beneficiary → submit an idempotent transfer/payment → API validates ownership and balance → transaction and balanced journal entries are committed together → customer sees the reference in history. This is internal demo money; no external payment rail is called.
3. **Business operations:** submit organization and financial records → prepare invoices, expense claims or payroll → authorized staff review items → settlement/ledger screens expose the local status and audit history.
4. **Risk and finance:** operations reviews seeded/synthetic signals and records human decisions → finance inspects journals, reconciliation differences and fee rules → changes are auditable.
5. **Planning and assistance:** customers set budgets/goals and view illustrative deposit projections; optional Copilot work requires consent and human review. Budgets/goals/deposits do not move funds, and AI does not make financial decisions.

All provider-dependent workflows remain simulated until real provider credentials, contracts, security controls and operational integrations are supplied. See [Phases 9–14](docs/phase-9-14.md) for data handling and deployment limits.

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

Replace the example `JWT_SECRET` in `.env` with a private random value before starting a shared environment. The demo accounts and password are for disposable local data only; replace or remove them before any shared environment.

Users can enable authenticator-app TOTP from **Security**. For a shared environment, set a stable `MFA_ENCRYPTION_KEY` as well; MFA secrets are encrypted at rest, and changing either encryption key requires affected users to enroll again.

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

### Demo accounts and walkthrough

After `python -m app.seed`, use these 25 fictional local demo users. Admin accounts use `admin12345678`; all other accounts use `FinSphere-Demo-2026!`. The seed command is safe to rerun: it adds missing demo rows without deleting existing data.

| Role | Username (email) | Display name |
| --- | --- | --- |
| Customer | `customer@finspherex.com` | Amina Demo |
| Customer | `customer2@finspherex.com` | Bilal Demo |
| Customer | `customer3@finspherex.com` | Sara Demo |
| Customer | `customer4@finspherex.com` | Hamza Demo |
| Customer | `customer5@finspherex.com` | Noor Demo |
| Customer | `customer6@finspherex.com` | Zain Demo |
| Operations | `operations@finspherex.com` | Operations Demo |
| Operations | `operations2@finspherex.com` | Operations Two Demo |
| Operations | `operations3@finspherex.com` | Operations Three Demo |
| Admin | `admin@finspherex.com` | Admin Demo |
| Admin | `admin2@finspherex.com` | Admin Two Demo |
| Business | `business@finspherex.com` | Business Demo |
| Business | `business2@finspherex.com` | Business Two Demo |
| Merchant | `merchant@finspherex.com` | Merchant Demo |
| Merchant | `merchant2@finspherex.com` | Merchant Two Demo |
| Customer | `customer7@finspherex.com` | Hira Demo |
| Customer | `customer8@finspherex.com` | Omar Demo |
| Customer | `customer9@finspherex.com` | Mariam Demo |
| Customer | `customer10@finspherex.com` | Usman Demo |
| Customer | `customer11@finspherex.com` | Zoya Demo |
| Customer | `customer12@finspherex.com` | Ibrahim Demo |
| Operations | `operations4@finspherex.com` | Operations Four Demo |
| Admin | `admin3@finspherex.com` | Admin Three Demo |
| Business | `business3@finspherex.com` | Business Three Demo |
| Merchant | `merchant3@finspherex.com` | Merchant Three Demo |

These credentials are for disposable local demo data only. Do not use them in a shared or production environment.

Every user has a sample customer profile, PKR account, and wallet. The seed also adds fictional transactions and balanced journal lines; payment history; cards in active and inactive states; pending KYC reviews with previewable documents clearly marked as demo samples; submitted and approved loan examples with repayment schedules; BNPL plans; business invoices, expenses, and payroll awaiting review; merchant sales, an open dispute, and settlement examples; an open risk case and screening result; a reconciliation variance; sample investment and remittance data; an open-banking consent; and masked developer/webhook test records. Values prefixed with `DEMO` are synthetic. These workflows simulate product behavior and do not move real funds or represent real customer documents.

Suggested walkthrough:

1. Sign in as `admin@finspherex.com` to explore all staff modules. Start at `/dashboard`, then visit `/kyc`, `/loans`, `/collections`, `/business-review`, `/payroll-review`, `/settlement-review`, `/expense-review`, `/merchant-disputes`, `/finance`, `/risk`, `/treasury`, `/remittance-review`, `/developer`, and `/members`.
2. Sign out and use `customer@finspherex.com` to see a customer account, card, transfer history, loan, BNPL plan, investment, remittance, and consent.
3. Use `customer8@finspherex.com` to inspect the KYC document upload and review flow. The preview document is fictional and visibly labelled as a demo.
4. Sign out and use `business@finspherex.com` or `merchant@finspherex.com` to see business and merchant workflows. `business3@finspherex.com` has a business profile awaiting review.

To create another member while signed in as an admin, open **Members & accounts** and submit the form. New customer accounts are provisioned with an account and wallet; new business and merchant profiles appear in their review workflow.

## Phase 5–8 feature screens

- Customer: `/loans` and `/bnpl` for illustrative installment requests/schedules.
- Business: `/business` for organization onboarding and invoice status; `/payroll` for payroll batches; `/merchant` for simulated settlement runs.
- Operations/admin: `/loans`, `/collections`, `/business-review`, `/payroll-review`, and `/settlement-review` for review queues; `/finance` for ledger, reconciliation and fee rules; `/risk` for casework and mock screening.
- These are local product simulations. Loan offers, payment acquiring, settlement movement, screening and regulatory decisions are not connected. See the [detailed implementation guide](docs/phase-5-8.md).

## Phase 9–11 feature screens

- Customer: `/investments`, `/fx-remittance`, `/copilot`, and `/open-banking`.
- Operations/admin: `/treasury` and `/remittance-review`; admin: `/developer` for test keys and sandbox webhook logs.
- Rates, investment entries and webhook deliveries remain local demos. The `/copilot` screen can use the OpenAI API when `OPENAI_API_KEY` is configured; otherwise it uses local fallback behavior. Review [the detailed guide](docs/phase-9-14.md) before using these interfaces.

To enable model assistance, set `OPENAI_API_KEY` in the API environment (or `.env` for Docker Compose). `OPENAI_MODEL` defaults to `gpt-6-astra`. Never expose the key to the browser. Copilot submissions require consent and are sent to the configured provider; transaction explanations send only limited transaction metadata. PDF, PNG, JPEG and WebP extraction is supported up to 6 MB, with uploads processed in memory. The model does not make financial decisions. See the [Phase 9–14 guide](docs/phase-9-14.md) for data handling details.

### Docker Compose

```bash
docker compose --profile observability up --build
```

This starts the web app, API, PostgreSQL, and optional Prometheus service with local-only credentials. Omit `--profile observability` to run the core app without Prometheus. Do not expose this configuration to a public network.

## Verify implementation

```bash
cd apps/api && pytest -q && ruff check app migrations tests && alembic upgrade head
cd ../..
corepack pnpm typecheck:web
corepack pnpm lint:web
corepack pnpm build:web
kubectl kustomize infrastructure/k8s/base
docker compose config
bash scripts/security-check.sh
k6 inspect performance/k6-smoke.js
```

Terraform formatting/validation and Playwright login browser tests are included in CI. Locally, install Chromium with `corepack pnpm --filter @finsphere/web exec playwright install chromium` before `corepack pnpm --filter @finsphere/web test:e2e`; Terraform checks require Terraform and an AWS provider download.

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
- Users can access only their own customer, account, wallet, beneficiary, card, transaction, and statement records. Operations endpoints use seeded role permissions. Access tokens are tied to revocable sessions, which users can review and end from Security.
- Card data stores only a generated last-four display value; no PAN or CVV is accepted or stored.
- KYC uploads are size/type limited and stored under a private local directory in this development phase.
- External payments, identity checks, email OTP, and card network processing are not connected. Authenticator-app TOTP MFA is supported. This release is a functional development prototype, not a regulated banking service.
