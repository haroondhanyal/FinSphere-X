"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function FinanceScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const finance = query.data as
    | {
        trial: {
          accounts: {
            code: string;
            name: string;
            currency: string;
            debit: string;
            credit: string;
          }[];
          debit_total: string;
          credit_total: string;
          balanced: boolean;
        };
        runs: {
          id: number;
          source: string;
          ledger_total: string;
          external_total: string;
          status: string;
          notes: string;
        }[];
        fees: {
          id: number;
          code: string;
          description: string;
          percentage: string;
          active: boolean;
        }[];
        journals: {
          id: number;
          reference: string;
          transaction_id: number;
          lines: {
            account_code: string;
            account_name: string;
            debit: string;
            credit: string;
          }[];
        }[];
      }
    | undefined;
  const trial = finance?.trial;
  const runs = finance?.runs ?? [];
  const fees = finance?.fees ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 7 · FINANCE"
        title="Ledger and reconciliation"
        copy="Inspect journal detail, reconcile control totals, and manage fee rules."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        <h3>Trial balance</h3>
        <p className="muted">
          Debits {money(trial?.debit_total ?? 0)} · credits{" "}
          {money(trial?.credit_total ?? 0)} ·{" "}
          {trial?.balanced ? "balanced" : "out of balance"}
        </p>
        {trial?.accounts.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Account</th>
                  <th>Debit</th>
                  <th>Credit</th>
                </tr>
              </thead>
              <tbody>
                {trial.accounts.map((row) => (
                  <tr key={row.code}>
                    <td>{row.code}</td>
                    <td>{row.name}</td>
                    <td>{money(row.debit, row.currency)}</td>
                    <td>{money(row.credit, row.currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="No posted ledger entries yet." />
        )}
      </div>
      <div className="panel">
        <h3>Recent journal entries</h3>
        {finance?.journals.length ? (
          finance.journals.map((entry) => (
            <div className="beneficiary-row" key={entry.id}>
              <span>
                <b>{entry.reference}</b>
                <small>
                  Transaction #{entry.transaction_id} ·{" "}
                  {entry.lines
                    .map(
                      (line) =>
                        `${line.account_code} D ${line.debit} / C ${line.credit}`,
                    )
                    .join(" · ")}
                </small>
              </span>
            </div>
          ))
        ) : (
          <Empty text="No journal entries." />
        )}
      </div>
      <form
        className="panel form-stack"
        onSubmit={submit(
          (d) =>
            api("/finance/reconciliation-runs", {
              method: "POST",
              body: JSON.stringify({
                source: d.get("source"),
                external_total: d.get("external_total"),
                notes: d.get("notes"),
              }),
            }),
          "Reconciliation result recorded.",
        )}
      >
        <h3>Run reconciliation</h3>
        <label>
          Source
          <input name="source" required defaultValue="daily-control" />
        </label>
        <label>
          External total
          <input
            name="external_total"
            type="number"
            min="0"
            step="0.01"
            required
          />
        </label>
        <label>
          Notes
          <input name="notes" maxLength={500} />
        </label>
        <button disabled={working}>Compare totals</button>
      </form>
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={submit(
            (d) =>
              api("/finance/fee-rules", {
                method: "POST",
                body: JSON.stringify({
                  code: d.get("code"),
                  description: d.get("description"),
                  percentage: d.get("percentage"),
                }),
              }),
            "Fee rule created.",
          )}
        >
          <h3>Add fee rule</h3>
          <label>
            Rule code
            <input name="code" pattern="[a-z0-9_-]+" required />
          </label>
          <label>
            Description
            <input name="description" required />
          </label>
          <label>
            Percentage
            <input
              name="percentage"
              type="number"
              min="0"
              max="100"
              step="0.01"
              required
            />
          </label>
          <button disabled={working}>Save rule</button>
          <p className="form-hint">
            New rules with code merchant_settlement apply to future simulated
            settlements.
          </p>
        </form>
        <div className="panel">
          <h3>Fee rules</h3>
          {fees.length ? (
            fees.map((fee) => (
              <div className="beneficiary-row" key={fee.id}>
                <span>
                  <b>
                    {fee.code} · {fee.percentage}%
                  </b>
                  <small>{fee.description}</small>
                </span>
                <StatePill value={fee.active ? "active" : "inactive"} />
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/finance/fee-rules/${fee.id}`, {
                          method: "PATCH",
                        }),
                      "Fee rule status updated.",
                    )
                  }
                >
                  {fee.active ? "Deactivate" : "Activate"}
                </button>
              </div>
            ))
          ) : (
            <Empty text="No fee rules configured." />
          )}
        </div>
      </div>
      <div className="panel">
        <h3>Recent reconciliation runs</h3>
        {runs.map((row) => (
          <div className="beneficiary-row" key={row.id}>
            <span>
              <b>{row.source}</b>
              <small>
                Ledger {money(row.ledger_total)} · external{" "}
                {money(row.external_total)}
              </small>
            </span>
            <StatePill value={row.status} />
          </div>
        ))}
      </div>
    </>
  );
}
