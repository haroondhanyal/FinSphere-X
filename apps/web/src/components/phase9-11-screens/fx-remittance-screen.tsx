"use client";

import { api, money } from "@/lib/api";
import { PageTitle, StatePill } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

export function FxRemittanceScreen(props: Phase911ScreenProps) {
  const { query, busy, result, notice, form } = props;
  const data = query.data as
    | {
        accounts: {
          id: number;
          account_number_masked: string;
          currency: string;
          balance: string;
        }[];
        remittances: {
          id?: number;
          destination_country?: string;
          source_amount?: string;
          source_currency?: string;
          destination_amount?: string;
          destination_currency?: string;
          status?: string;
        }[];
      }
    | undefined;
  return (
    <>
      <PageTitle
        eyebrow="PHASE 9 · FX & REMITTANCE"
        title="FX calculator and remittance"
        copy="Preview static sandbox rates and submit requests for operations review."
      />
      {notice}
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={form(
            (d) =>
              api(
                `/fx/quote?source_currency=${d.get("source_currency")}&destination_currency=${d.get("destination_currency")}&amount=${d.get("amount")}`,
              ),
            "Static FX quote calculated.",
          )}
        >
          <h3>Rate calculator</h3>
          <label>
            Amount
            <input
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            From
            <select name="source_currency">
              <option>PKR</option>
              <option>USD</option>
              <option>EUR</option>
            </select>
          </label>
          <label>
            To
            <select name="destination_currency">
              <option>USD</option>
              <option>PKR</option>
              <option>EUR</option>
              <option>AED</option>
            </select>
          </label>
          <button disabled={busy}>Get quote</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (d) =>
              api("/remittances", {
                method: "POST",
                body: JSON.stringify({
                  source_account_id: Number(d.get("account_id")),
                  amount: d.get("amount"),
                  destination_country: d.get("country"),
                }),
              }),
            "Remittance request sent for review.",
          )}
        >
          <h3>Request remittance</h3>
          <label>
            Source account
            <select name="account_id">
              {(data?.accounts ?? []).map((account) => (
                <option value={account.id} key={account.id}>
                  {account.account_number_masked} · {account.currency} ·{" "}
                  {money(account.balance, account.currency)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Amount
            <input
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            Destination country
            <select name="country">
              <option value="US">United States</option>
              <option value="GB">United Kingdom</option>
              <option value="AE">United Arab Emirates</option>
              <option value="EU">Euro area</option>
              <option value="SA">Saudi Arabia</option>
            </select>
          </label>
          <button disabled={busy}>Submit request</button>
          <p className="form-hint">
            No balance debit or international transfer is made.
          </p>
        </form>
      </div>
      {result && <pre className="panel">{JSON.stringify(result, null, 2)}</pre>}
      <div className="panel">
        <h3>Remittance history</h3>
        {data?.remittances.map((row) => (
          <div className="beneficiary-row" key={row.id}>
            <span>
              <b>
                {row.destination_country} ·{" "}
                {money(row.source_amount ?? 0, row.source_currency)}
              </b>
              <small>
                Receive{" "}
                {money(row.destination_amount ?? 0, row.destination_currency)} ·{" "}
                {row.destination_currency}
              </small>
            </span>
            <StatePill value={row.status ?? "unknown"} />
          </div>
        ))}
      </div>
    </>
  );
}
