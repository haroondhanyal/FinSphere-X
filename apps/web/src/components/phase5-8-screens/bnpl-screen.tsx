"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Bnpl } from "./domain-types";
import type { Phase58ScreenProps } from "./types";

export function BnplScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, submit } = props;
  const plans = (query.data as Bnpl[] | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 5 · BUY NOW, PAY LATER"
        title="BNPL plans"
        copy="Create a sample installment plan and track its schedule."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={submit(
            (d) =>
              api("/bnpl/plans", {
                method: "POST",
                body: JSON.stringify({
                  merchant_name: d.get("merchant_name"),
                  amount: d.get("amount"),
                  currency: d.get("currency"),
                  installments: Number(d.get("installments")),
                }),
              }),
            "BNPL plan created.",
          )}
        >
          <h3>Create a simulated plan</h3>
          <label>
            Merchant
            <input name="merchant_name" required />
          </label>
          <label>
            Purchase amount
            <input
              name="amount"
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
          <label>
            Installments
            <input
              name="installments"
              type="number"
              min="2"
              max="12"
              defaultValue="4"
            />
          </label>
          <button disabled={working}>Create plan</button>
          <p className="form-hint">
            No credit decision, financing or funds movement is performed.
          </p>
        </form>
        <div className="panel">
          <h3>Your plans</h3>
          {plans.length ? (
            plans.map((plan) => (
              <div className="beneficiary-row" key={plan.id}>
                <span>
                  <b>
                    {plan.merchant_name} ·{" "}
                    {money(plan.purchase_amount, plan.currency)}
                  </b>
                  <small>
                    {plan.installment_count} installments ·{" "}
                    {money(plan.installment_amount, plan.currency)} each
                  </small>
                  {plan.installments.map((part) => (
                    <small key={part.id}>
                      #{part.installment_number}:{" "}
                      {money(part.amount, plan.currency)} · {part.status}
                    </small>
                  ))}
                </span>
                <StatePill value={plan.status} />
              </div>
            ))
          ) : (
            <Empty text="No BNPL plans yet." />
          )}
        </div>
      </div>
    </>
  );
}
