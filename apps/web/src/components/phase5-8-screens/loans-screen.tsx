"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Loan, LoanProduct } from "./domain-types";
import type { Phase58ScreenProps } from "./types";

export function LoansScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const loanData = query.data as
    | {
        applications: Loan[];
        can_review: boolean;
        can_manage_products: boolean;
        products: LoanProduct[];
      }
    | undefined;
  const loans = loanData?.applications ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 5 · LENDING"
        title="Loans"
        copy="Request an illustrative loan estimate and track review status."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      {loanData?.can_manage_products && (
        <form
          className="panel form-stack"
          onSubmit={submit(
            (d) =>
              api("/loans/products", {
                method: "POST",
                body: JSON.stringify({
                  code: d.get("code"),
                  name: d.get("name"),
                  description: d.get("description"),
                  annual_rate: d.get("annual_rate"),
                  minimum_amount: d.get("minimum_amount"),
                  maximum_amount: d.get("maximum_amount"),
                  minimum_term_months: Number(d.get("minimum_term_months")),
                  maximum_term_months: Number(d.get("maximum_term_months")),
                }),
              }),
            "Loan product created.",
          )}
        >
          <h3>Add loan product</h3>
          <label>
            Code
            <input name="code" required />
          </label>
          <label>
            Name
            <input name="name" required />
          </label>
          <label>
            Description
            <input name="description" required />
          </label>
          <label>
            APR percent
            <input
              name="annual_rate"
              type="number"
              min="0"
              max="100"
              step="0.01"
              required
            />
          </label>
          <label>
            Minimum amount
            <input
              name="minimum_amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            Maximum amount
            <input
              name="maximum_amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </label>
          <label>
            Term range in months
            <input
              name="minimum_term_months"
              type="number"
              min="1"
              max="360"
              required
            />
            <input
              name="maximum_term_months"
              type="number"
              min="1"
              max="360"
              required
            />
          </label>
          <button disabled={working}>Create product</button>
        </form>
      )}
      <div className="two-column">
        {!loanData?.can_review && (
          <form
            className="panel form-stack"
            onSubmit={submit(
              (d) =>
                api<Loan>("/loans/applications", {
                  method: "POST",
                  body: JSON.stringify({
                    product_code: d.get("product_code"),
                    purpose: d.get("purpose"),
                    amount: d.get("amount"),
                    currency: d.get("currency"),
                    term_months: Number(d.get("term_months")),
                  }),
                }),
              "Application submitted.",
            )}
          >
            <h3>Choose a product and apply</h3>
            <label>
              Loan product
              <select name="product_code" required>
                {(loanData?.products ?? []).map((product) => (
                  <option key={product.code} value={product.code}>
                    {product.name} · {product.annual_rate}% APR ·{" "}
                    {product.minimum_term_months}–{product.maximum_term_months}{" "}
                    months
                  </option>
                ))}
              </select>
            </label>
            <label>
              Purpose
              <input name="purpose" required minLength={4} />
            </label>
            <label>
              Amount
              <input name="amount" type="number" min="1" step="0.01" required />
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
              Term (months)
              <input
                name="term_months"
                type="number"
                min="3"
                max="360"
                defaultValue="12"
                required
              />
            </label>
            <button disabled={working || !loanData?.products.length}>
              Submit application
            </button>
            <p className="form-hint">
              Estimates and products are illustrative; this is not a credit
              offer.
            </p>
          </form>
        )}
        <div className="panel">
          <h3>Applications</h3>
          {query.isLoading ? (
            <p className="muted">Loading…</p>
          ) : loans.length ? (
            loans.map((loan) => (
              <div className="beneficiary-row" key={loan.id}>
                <span>
                  <b>{loan.purpose}</b>
                  <small>
                    {money(loan.amount, loan.currency)} · {loan.term_months}{" "}
                    months · est.{" "}
                    {money(loan.estimated_monthly_payment, loan.currency)}/mo
                  </small>
                  <small>
                    Demo-only request score: {loan.illustrative_score ?? "—"} ·{" "}
                    {loan.score_reasons}
                  </small>
                  {loan.installments?.length ? (
                    <small>
                      Repayment schedule: {loan.installments.length} monthly
                      installments
                    </small>
                  ) : null}
                </span>
                <StatePill value={loan.status} />
                {loan.can_review && loan.status === "submitted" && (
                  <div className="inline-actions">
                    {["approved", "declined", "more_information_required"].map(
                      (decision) => (
                        <button
                          key={decision}
                          disabled={working}
                          onClick={() =>
                            void perform(
                              () =>
                                api(`/loans/applications/${loan.id}`, {
                                  method: "PATCH",
                                  body: JSON.stringify({ decision }),
                                }),
                              `Application ${decision.replaceAll("_", " ")}.`,
                            )
                          }
                        >
                          {decision.replaceAll("_", " ")}
                        </button>
                      ),
                    )}
                  </div>
                )}
                {!loan.can_review &&
                  loan.installments
                    ?.filter(
                      (item) =>
                        item.status === "scheduled" ||
                        item.status === "overdue",
                    )
                    .map((item) => (
                      <button
                        key={item.id}
                        disabled={working}
                        onClick={() =>
                          void perform(
                            () =>
                              api(
                                `/loans/installments/${item.id}/record-payment`,
                                { method: "POST" },
                              ),
                            "Demo installment payment recorded.",
                          )
                        }
                      >
                        Record installment {item.installment_number} demo
                        payment
                      </button>
                    ))}
              </div>
            ))
          ) : (
            <Empty text="No loan applications yet." />
          )}
        </div>
      </div>
    </>
  );
}
