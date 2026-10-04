# Web screen ownership for an 8-person team

Each screen owner works in their own screen files. The screen dispatcher and shared contracts stay with the integrator to avoid merge conflicts. All paths are relative to the repository root.

| Developer                         | Screen ownership                                                                   | Files                                                                                                                                                                |
| --------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 · Overview                      | Customer dashboard                                                                 | `apps/web/src/components/customer-screens/dashboard-screen.tsx`                                                                                                      |
| 2 · Accounts                      | Account list/detail and statements                                                 | `apps/web/src/components/customer-screens/accounts-screen.tsx`, `apps/web/src/components/account-detail-screen.tsx`, `apps/web/src/components/statements-screen.tsx` |
| 3 · Everyday money                | Wallet, transfers and payments                                                     | `apps/web/src/components/customer-screens/wallet-screen.tsx`, `apps/web/src/components/customer-screens/transfer-screen.tsx`                                         |
| 4 · Cards                         | Card issue, freeze, limits and status                                              | `apps/web/src/components/customer-screens/cards-screen.tsx`                                                                                                          |
| 5 · Identity                      | Profile, security and KYC queue                                                    | `apps/web/src/components/customer-screens/profile-security-screen.tsx`, `apps/web/src/components/customer-screens/kyc-queue-screen.tsx`                              |
| 6 · Lending                       | Loans, BNPL and collections                                                        | `apps/web/src/components/phase5-8-screens/loans-screen.tsx`, `bnpl-screen.tsx`, `collections-screen.tsx`                                                             |
| 7 · Business and operations       | Business, payroll, expenses, merchant, finance, risk and reviews                   | `apps/web/src/components/phase5-8-screens/` — edit only the screen files for your route                                                                              |
| 8 · New products and integrations | Investments, FX/remittance, treasury, copilot, open banking and developer platform | `apps/web/src/components/phase9-11-screens/` — edit only the screen files for your route                                                                             |

## How a screen is wired

- One route view lives in one `*-screen.tsx` file. Add markup and screen-specific interactions there.
- The `phase5-8-screen.tsx` and `phase9-11-screen.tsx` files load data and dispatch it to a screen component. The customer `module-screen.tsx` does the same for core screens. Avoid adding page markup or screen-specific layout to these dispatchers.
- Each screen group has a `types.ts` contract for props/actions. Add a prop there when a screen needs data from its dispatcher.
- `screen-primitives.tsx` holds shared display components and `screen-actions.tsx` holds reusable controls. Developer 8 reviews changes that affect other screens.
- `workspace-navigation.ts`, `workspace-sidebar.tsx`, and `workspace-header.tsx` are the authenticated shell.

## Local checks before handoff

Run from the repository root:

```sh
corepack pnpm --filter @finsphere/web typecheck
corepack pnpm --filter @finsphere/web lint
```
