# FinSphere X — product screens and delivery roadmap

## Product shape

Use one web app with role-aware navigation and shared UI. Keep customer, business, merchant, operations, and administration areas as route groups inside the web app at first. Split them into separately deployed apps only when ownership, security boundaries, or release needs justify it. This avoids duplicating login, design, and API code across seven apps.

## Screen inventory

### Shared entry and shell

- `/login`: email/password, OTP/MFA challenge, remember-device choice, validation and error states.
- `/register`: account type selection and initial identity/contact details.
- `/onboarding`: stepper for contact verification, profile, address, identity documents, income, terms, and review status.
- Shared authenticated shell: role-aware sidebar, top bar, global search, notifications, profile menu, theme switch, breadcrumbs, and responsive navigation drawer.
- `/dashboard`: role-specific home; customer balance and activity, business cash position and approvals, merchant sales and settlement, or operations queues.
- `/profile`, `/security`, `/notifications`, `/support`: profile, sessions/devices/MFA, preferences, and support cases.

### Retail customer

- `/accounts`, `/accounts/[id]`: account list and account detail with available/ledger balance, masked identifiers, activity, and statement action.
- `/wallet`: balance, limits, add/withdraw/send/receive and wallet history.
- `/transfers/new`, `/transfers`, `/beneficiaries`: validated transfer wizard (source, recipient, amount, fee/FX preview, confirmation, result), history, and saved recipients.
- `/payments`: billers, utility/mobile payments, invoices, and payment history.
- `/cards`, `/cards/[id]`: masked card, controls, limits, status, and activity.
- `/loans`, `/loans/apply`, `/loans/[id]`: eligible products, application steps, offer, repayment schedule, and servicing.
- `/deposits`, `/investments`: product list, positions, maturity/returns, and simulated-market disclosures.
- `/budget`, `/goals`: spending categories, budget remaining/forecast, and goal progress.
- `/statements`: date/account filters and generated export status.

### Business and merchant

- `/business/dashboard`: cash flow, receivables/payables, approvals, upcoming payroll, and account summary.
- `/business/accounts`, `/business/payments`, `/business/payroll`: organization accounts, bulk payment review, payroll validation and approval.
- `/business/invoices`, `/business/expenses`, `/business/cards`: invoice lifecycle, receipt claims, and employee card controls.
- `/business/approvals`: maker/checker queue, detail, evidence, decision, and audit timeline.
- `/business/cashflow`, `/business/reports`: forecast assumptions and downloadable reports.
- `/merchant/dashboard`, `/merchant/transactions`, `/merchant/refunds`: sales, transaction search, refund review.
- `/merchant/settlements`, `/merchant/chargebacks`, `/merchant/invoices`, `/merchant/settings`: payout batches, evidence workflow, invoice tracking, terminals and configuration.

### Operations, risk and administration

- `/ops/dashboard`, `/ops/payments`, `/ops/reconciliation`, `/ops/settlements`: exception queues, detail workbench, matching, and batch state.
- `/ops/kyc`, `/ops/fraud`, `/ops/aml`: review queues, case detail, evidence, notes, decision and audit trail.
- `/ops/loans`, `/ops/support`: assigned applications and customer support workspace.
- `/admin/dashboard`, `/admin/customers`, `/admin/accounts`, `/admin/cards`, `/admin/loans`, `/admin/payments`, `/admin/merchants`: searchable operational records and permitted actions.
- `/admin/fraud`, `/admin/aml`, `/admin/reconciliation`, `/admin/settlement`, `/admin/ledger`: oversight and controlled work queues.
- `/admin/products`, `/admin/fees`, `/admin/roles`, `/admin/audit`, `/admin/settings`: configuration with validation, preview, effective dates and audit history.
- `/developer`: API applications, credentials lifecycle, sandbox, docs, webhook endpoints, delivery logs and usage.

### Shared screen states

Every list/detail screen needs loading, empty, error, forbidden, and stale-data states. Tables need search/filter/sort/pagination and clear status badges. Destructive or financial actions need confirmation and a final server response. Keep identifiers masked by default and reveal only with a permission check and audit event.

## 14 delivery phases

Each phase should be a releasable vertical slice. Close a phase only after its UI, API, database migration, validation, permissions, audit needs, docs, and requested quality checks are complete.

| Phase | Scope                                                        | Main screens / result                                                            |
| ----- | ------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| 1     | Monorepo, authentication, RBAC, base UI, database            | Login, protected shell, role-aware dashboard, users/roles/permissions foundation |
| 2     | Customers, KYC/KYB, accounts, wallet                         | Onboarding, review queue, customer profile, account detail, wallet               |
| 3     | Transfers, payments, beneficiaries, ledger                   | Transfer wizard, payment history, beneficiaries, balanced posting foundation     |
| 4     | Cards, virtual cards, statements                             | Card list/detail/control, statements                                             |
| 5     | Loans, mock credit decision support, BNPL, collections       | Application/underwriting, schedules, servicing, collections queue                |
| 6     | Business banking, merchant, invoices, payroll                | Organization dashboard, approvals, invoice/payroll, merchant settlement view     |
| 7     | Accounting, general ledger, fees, reconciliation, settlement | Finance workbench, journals, fee configuration, matching/batches                 |
| 8     | Fraud, AML, risk, compliance                                 | Alert queues, case workspace, screening mock, decisions and audit                |
| 9     | Investments, treasury, FX, remittance                        | Portfolio, liquidity, rate calculator, remittance review                         |
| 10    | AI copilot, document AI, forecasting                         | Explain/summarize views with source context and human review                     |
| 11    | Open banking, developer APIs, webhooks                       | Consent, API client, sandbox docs and delivery logs                              |
| 12    | Automation, performance, security checks                     | Playwright, API/DB checks, k6 scenarios, security regression suite               |
| 13    | Docker, CI/CD, observability                                 | Local stack, CI workflows, metrics/traces/logs                                   |
| 14    | Kubernetes, Terraform, cloud architecture                    | Deployment templates and cloud infrastructure baseline                           |

## Team of 10–12 developers

Use a tech lead/architect to own contracts, reviews, and integration; one product designer to keep screen flows consistent (shared across the team); and these engineering workstreams:

| Workstream                       | People | Owns                                                                                 |
| -------------------------------- | -----: | ------------------------------------------------------------------------------------ |
| Frontend shell and design system |      2 | Navigation, shared components, accessibility, responsive behavior, theme             |
| Customer web                     |      2 | Retail onboarding, accounts, wallet, transfers and customer-facing flows             |
| Business and merchant web        |      2 | Organizations, approvals, invoices, payroll, merchant flows                          |
| API and identity                 |      2 | FastAPI modules, auth, authorization, DTOs, API contracts                            |
| Data and ledger                  |      2 | PostgreSQL models/migrations, transaction boundaries, ledger correctness             |
| Quality and platform             |    1–2 | CI, integration/e2e automation, local environment, observability and security checks |

For a 10-person team, combine one frontend slot with platform and have the tech lead contribute to API integration. At 12, add one frontend engineer and one QA/platform engineer. Assign a named owner and reviewer to each module; keep API contracts in OpenAPI before parallel UI and API implementation starts.

## Simple code organization

Keep files small and group by feature. UI pages call typed API hooks; API routes validate DTOs and permissions, then call services; services own business rules and transaction boundaries; repositories isolate database queries. Shared packages should hold only genuinely shared code.

```text
apps/
  web/                 # Next.js: app routes, features, shared UI
  api/                 # FastAPI: routers, schemas, services, repositories
packages/
  ui/                  # reusable visual components
  contracts/           # generated/shared API types
  config/              # lint, formatting and TypeScript config
infrastructure/        # local compose, CI, later cloud manifests
docs/
```

Avoid one giant dashboard component, one generic API service for every module, and premature microservices. Extract a module when it has a real scaling, ownership, or security need.

## Phase 1 definition of done

- Monorepo and VS Code setup documented, repeatable local start commands.
- Login/session boundary and backend permission checks; frontend route checks are usability controls, not the security boundary.
- Seed roles/permissions are fictional and least-privilege; no public demo passwords committed.
- Base responsive shell and role-specific dashboard placeholders clearly marked as not-yet-connected where applicable.
- PostgreSQL migrations for identity/RBAC and audit foundation; secrets loaded from environment.
- API schemas validated; lint/typecheck and focused auth/permission checks pass.
- README and OpenAPI setup instructions are current.

## Delivery command policy

When dependencies are added, record the exact VS Code terminal command in the phase handoff. Keep Node dependencies under `pnpm` and Python dependencies under `uv`; pin and review versions as they are selected. Do not claim a phase is complete until commands have actually been run and the results recorded.
