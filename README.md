<p align="center">
  <a href="https://github.com/haroondhanyal/FinSphere-X">
    <img src="https://raw.githubusercontent.com/haroondhanyal/FinSphere-X/main/assets/finsphere-x-logo.svg" alt="FinSphere X — Banking Beyond Borders" width="520" />
  </a>
</p>

<h1 align="center">FinSphere X</h1>
<p align="center"><strong>AI-Powered Digital Banking &amp; Financial Operations Platform</strong></p>
<p align="center"><a href="https://github.com/haroondhanyal/FinSphere-X">GitHub Repository</a> · Banking Beyond Borders</p>

FinSphere X brings digital banking, payments, business finance, and financial operations together in one role-aware platform. Development is organized into 14 incremental phases so each module can be built, reviewed, and connected without starting with a complex distributed system.

## Project status

Roadmap and architecture foundation. Product screens and delivery ownership are documented in [the roadmap](docs/roadmap.md). Planned modules are not represented as implemented features until their code and checks are complete.

## Roadmap — 14 phases

| Phase | Delivery |
|---|---|
| 1 | Monorepo, authentication, RBAC, base UI, database |
| 2 | Customers, KYC/KYB, accounts, wallet |
| 3 | Transfers, payments, beneficiaries, ledger |
| 4 | Cards, virtual cards, statements |
| 5 | Loans, mock credit decision support, BNPL, collections |
| 6 | Business banking, merchant, invoices, payroll |
| 7 | Accounting, general ledger, fees, reconciliation, settlement |
| 8 | Fraud, AML, risk, compliance |
| 9 | Investments, treasury, FX, remittance |
| 10 | AI copilot, document AI, forecasting |
| 11 | Open banking, developer APIs, webhooks |
| 12 | Automation, performance, security testing |
| 13 | Docker, CI/CD, observability |
| 14 | Kubernetes, Terraform, cloud architecture |

## Documentation

- [Detailed screen inventory, phase plan, and team split](docs/roadmap.md)
- [Architecture and coding conventions](docs/architecture.md)

## Engineering principles

- Start as a modular monolith: Next.js web app, FastAPI API, and PostgreSQL.
- Keep feature code small and group it by module; validate requests at the API boundary.
- Enforce permissions and tenant ownership in the backend.
- Use `Decimal` and PostgreSQL `NUMERIC` for money.
- Financial posting must be atomic, idempotent, auditable, and balanced.
- Never store raw CVV, plain-text passwords, or secrets in the repository.
