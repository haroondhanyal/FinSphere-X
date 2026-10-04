"use client";

import { api, money } from "@/lib/api";
import { Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function MerchantScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, submit } = props;
  const settlements =
    (query.data as
      | {
          id: number;
          reference: string;
          gross_amount: string;
          fee_amount: string;
          net_amount: string;
          currency: string;
          status: string;
          disclosure: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 6 · MERCHANT"
        title="Merchant settlements"
        copy="Review settlement runs. Processing is simulated and does not move funds."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        <form
          className="form-stack"
          onSubmit={submit(
            (d) =>
              api("/merchant/settlements", {
                method: "POST",
                body: JSON.stringify({
                  gross_amount: d.get("gross_amount"),
                  currency: d.get("currency"),
                }),
              }),
            "Simulated settlement run created.",
          )}
        >
          <h3>Simulate a settlement</h3>
          <label>
            Gross sales
            <input
              name="gross_amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            Currency
            <select name="currency">
              <option>PKR</option>
              <option>USD</option>
              <option>EUR</option>
            </select>
          </label>
          <button disabled={working}>Create settlement</button>
          <p className="form-hint">Illustrative 1.5% fee. No funds move.</p>
        </form>
        {settlements.map((row) => (
          <div className="beneficiary-row" key={row.id}>
            <span>
              <b>{row.reference}</b>
              <small>
                Gross {money(row.gross_amount, row.currency)} · fee{" "}
                {money(row.fee_amount, row.currency)} · net{" "}
                {money(row.net_amount, row.currency)}
              </small>
            </span>
            <StatePill value={row.status} />
          </div>
        ))}
      </div>
    </>
  );
}
