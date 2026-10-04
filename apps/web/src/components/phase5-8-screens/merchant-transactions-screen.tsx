"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function MerchantTransactionsScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const rows =
    (query.data as
      | {
          id: number;
          reference: string;
          description: string;
          amount: string;
          currency: string;
          status: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 6 · MERCHANT SALES"
        title="Transactions and refunds"
        copy="Create test sales, inspect transaction status, and record simulated refunds."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <form
        className="panel form-stack"
        onSubmit={submit(
          (d) =>
            api("/merchant/sales", {
              method: "POST",
              body: JSON.stringify({
                description: d.get("description"),
                amount: d.get("amount"),
                currency: d.get("currency"),
              }),
            }),
          "Demo sale recorded.",
        )}
      >
        <h3>Create a test sale</h3>
        <label>
          Description
          <input name="description" required />
        </label>
        <label>
          Amount
          <input name="amount" type="number" min="0.01" step="0.01" required />
        </label>
        <label>
          Currency
          <select name="currency">
            <option>PKR</option>
            <option>USD</option>
            <option>EUR</option>
          </select>
        </label>
        <button disabled={working}>Record demo sale</button>
        <p className="form-hint">No card payment is processed.</p>
      </form>
      <div className="panel">
        {rows.length ? (
          rows.map((row) => (
            <div className="beneficiary-row" key={row.id}>
              <span>
                <b>
                  {row.reference} · {row.description}
                </b>
                <small>{money(row.amount, row.currency)}</small>
              </span>
              <StatePill value={row.status} />
              {row.status === "captured_demo" && (
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/merchant/sales/${row.id}/refund`, {
                          method: "POST",
                        }),
                      "Demo refund recorded.",
                    )
                  }
                >
                  Refund (demo)
                </button>
              )}
            </div>
          ))
        ) : (
          <Empty text="No merchant sales." />
        )}
      </div>
    </>
  );
}
