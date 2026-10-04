# Phase 9–14 implementation guide

These phases add local sandbox features plus CI and infrastructure templates to the modular monolith. Apply `alembic upgrade head` and run `python -m app.seed` before starting the API; the seed creates two illustrative investment products. Market, banking and webhook functions remain sandbox-only. Phase 10 can call the OpenAI Responses API when configured; otherwise it uses local fallbacks.

## Customer workspace utilities

- `/onboarding` is a checklist backed by the customer profile and KYC review state. `/support` stores customer-owned tickets and allows operations/admin staff to respond; it does not send email or push notifications.
- `/notifications` is a recent audit-activity feed. It currently has no read/unread tracking or delivery channel.
- `/budgets` stores monthly spending limits and totals matching posted local transactions. `/goals` tracks user-entered progress; recording progress does not transfer or reserve funds.
- `/deposits` records illustrative PKR term-deposit projections. It checks the selected account and amount but does not debit or reserve the account balance or place a deposit.
- `/search` searches only the signed-in customer's local accounts, transactions, beneficiaries and cards.
- APIs: `/api/v1/support/tickets`, `/api/v1/notifications`, `/api/v1/budgets`, `/api/v1/goals`, `/api/v1/deposits/*`, and `/api/v1/search`.

## Phase 9: investments, treasury, FX and remittance

- `/investments` lists illustrative products and a sample portfolio; positions do not debit an account or buy an asset.
- `/treasury` is operations/admin only and sums active local account balances by currency.
- `/fx-remittance` calculates from a static demo rate table and creates a remittance request. Operations review changes its status only.
- APIs: `/api/v1/investments/*`, `/api/v1/treasury/liquidity`, `/api/v1/fx/quote`, `/api/v1/remittances`.

## Phase 10: copilot, document extraction and forecast

- `/copilot` shows a source-linked transaction explanation, source summary, amount/date extraction from pasted text, and a historical-average forecast with an optional AI explanation.
- Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in the API environment to enable model assistance. The key stays on the API server. Without a key, the screens use local fallback behavior.
- Users confirm before submitting source text or limited transaction data. Only the transaction type, amount, currency, status and timestamp are sent for a transaction explanation; customer names and transaction references are omitted. Source text is sent as entered. Do not submit information without authorization.
- Human review is required. The model cannot approve transactions, decide credit, or provide financial advice. With an API key, document extraction accepts pasted text and PDF/PNG/JPEG/WebP uploads (maximum 6 MB); uploads are processed in memory and not persisted by this endpoint. PDF/image contents are sent to the configured provider. Without a key, pasted-text extraction falls back locally and uploads are unavailable. The application computes forecast arithmetic; AI only explains the supplied aggregate.
- APIs: `/api/v1/copilot/transactions/{id}/explanation`, `/api/v1/copilot/summarize`, `/api/v1/copilot/documents/extract`, `/api/v1/copilot/forecast`.

## Phase 11: open banking and developer sandbox

- `/open-banking` creates and revokes scoped, expiring local consent records against fictional providers.
- `/developer` creates/revokes one-time-display test API keys, records HTTPS webhook endpoints, and creates local queued delivery log entries.
- API client secrets are stored as hashes and authenticate read-only `GET /api/v1/developer/v1/me`, `/accounts`, and `/transactions` sandbox routes via `X-API-Key`. They cannot authorize money movement. Webhook test deliveries never call the configured URL.
- APIs: `/api/v1/open-banking/*` and `/api/v1/developer/*`.

## Phase 12: quality and security automation

- GitHub Actions runs API tests, Ruff, SQLite migration, web typecheck/lint/build, Playwright Chromium browser tests, Terraform validation, local pip audit, source secret-pattern checks, and API/web image builds.
- `apps/api/tests/test_phase_9_11.py` covers investment ownership/no-debit, remittance and consent ownership, key revocation, and sandbox delivery records.
- `apps/web/e2e/login.spec.ts` checks the mobile login form and session-token handling. Install Chromium with `corepack pnpm --filter @finsphere/web exec playwright install chromium`, then run `corepack pnpm --filter @finsphere/web test:e2e`.
- `performance/k6-smoke.js` checks health and OpenAPI latency/error thresholds. Run with `k6 run performance/k6-smoke.js` against a local API.

## Phase 13: containers and observability

- Docker Compose starts API, web and PostgreSQL; start the optional Prometheus service with `--profile observability`. The API exposes `/health`, DB-backed `/ready`, request ID headers and low-cardinality Prometheus counters at `/metrics`.
- API and web images run as non-root. For a production web image, build with `--build-arg NEXT_PUBLIC_API_URL=https://api.example.com/api/v1` because Next.js embeds this public value at build time.
- Local Compose credentials are disposable. KYC files are local/ephemeral; use private object storage before shared deployment.

## Phase 14: Kubernetes and Terraform baseline

- `infrastructure/k8s/base` contains Kustomize namespace, API/web deployments and services, probes, resource limits, non-root controls, HPA and TLS ingress. Create namespace secrets named `finspherex-secrets` out of band.
- Apply `infrastructure/k8s/migration-job.yaml` before deploying workloads. Set real images, hosts, TLS, secret values, CORS origin and build-time public API URL first.
- `infrastructure/terraform` defines a private VPC/subnets, Postgres RDS baseline and restricted database security group. It expects an existing application workload security group and managed Kubernetes cluster.
- Terraform is validated as configuration only; it has not been applied. Configure an encrypted remote state backend and secret manager, inspect the plan/cost, and obtain environment-specific approvals before provisioning.

## Local verification

```bash
cd apps/api && pytest -q && ruff check app migrations tests
cd ../.. && corepack pnpm typecheck:web && corepack pnpm lint:web && corepack pnpm build:web
corepack pnpm --filter @finsphere/web test:e2e
kubectl kustomize infrastructure/k8s/base
terraform -chdir=infrastructure/terraform fmt -check -recursive
terraform -chdir=infrastructure/terraform init -backend=false && terraform -chdir=infrastructure/terraform validate
```
