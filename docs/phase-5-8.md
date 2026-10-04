# Phase 5–8 implementation guide

Phases 5–8 are functional local-development slices on the existing FastAPI, SQLAlchemy, PostgreSQL/SQLite and Next.js stack. Apply the migrations and seed role accounts using the Phase 1–4 commands in the [README](../README.md), then start the API and web app. Additive migrations `0003_phases_5_8` through `0006_loan_decision_support` preserve the Phase 1–4 contracts.

## Phase 5: lending

- Customer routes `/loans` and `/bnpl` show the seeded product catalog, illustrative request score/payment estimate, repayment schedules and BNPL plans.
- Operations/admin review applications; approved demo loans create installment schedules. `/collections` tracks loan/BNPL due dates and lets staff record demo collections.
- API: `/api/v1/loans/products`, `/api/v1/loans/applications`, `/api/v1/loans/collections`, `/api/v1/bnpl/plans`, `/api/v1/bnpl/collections`.
- The score is a synthetic request-shape heuristic, not borrower underwriting. No bureau data, binding offer, agreement, disbursement or funds collection is performed.

## Phase 6: business and merchant

- Role-specific business dashboard summarizes invoice receivables, payroll and expense queues. Business routes `/business`, `/payroll`, and `/expenses` provide organization review, invoice paid/refund states, payroll maker-checker, and expense evidence references.
- Merchant routes `/merchant`, `/merchant-transactions`, and `/merchant-disputes` cover sales search, demo refunds, dispute/chargeback evidence, and settlement review. Operations/admin dashboards link to each approval queue.
- API includes `/api/v1/business/summary`, `/api/v1/business/organizations`, `/api/v1/business/invoices`, `/api/v1/business/payroll`, `/api/v1/business/expenses`, `/api/v1/merchant/summary`, `/api/v1/merchant/sales`, `/api/v1/merchant/disputes`, and `/api/v1/merchant/settlements`.
- Records model approval and evidence references. No acquiring, invoice payment, payroll, refund, payout or settlement moves money.

## Phase 7: finance operations

- Operations/admin route `/finance` shows trial balance and journal lines, records control-total reconciliation runs, configures percentage fee rules, and applies the active `merchant_settlement` rule to new settlement simulations.
- API: `/api/v1/finance/trial-balance`, `/api/v1/finance/journals`, `/api/v1/finance/reconciliation-runs`, and `/api/v1/finance/fee-rules`.
- Reconciliation compares a submitted external total to posted journal debits for the local ledger. It is not connected to a bank feed or settlement provider.

## Phase 8: risk and compliance

- Operations/admin route `/risk` records fraud/AML/sanctions cases, runs a synthetic keyword screening fixture, stores reviewer notes and evidence references, and records a human decision. All actions create audit records.
- API: `/api/v1/risk/cases`, `/api/v1/risk/screenings`, and case note/evidence actions.
- No screening vendor, production rules engine, AI decision, regulatory filing or external identity check is connected. Mock matches must be manually reviewed.

## Demo roles

`python -m app.seed` creates customer, operations, admin, business and merchant users, plus the illustrative merchant settlement fee rule, using the local demo password documented in the README. They are disposable local accounts; replace/remove them and set a private `JWT_SECRET` before any shared environment.

## Verification commands

```bash
cd apps/api
pytest -q
ruff check .
cd ../..
corepack pnpm typecheck:web
corepack pnpm lint:web
corepack pnpm build:web
```
