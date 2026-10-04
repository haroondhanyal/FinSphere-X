"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function BusinessScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const business = query.data as
    | {
        profile: { id: number; legal_name: string; status: string } | null;
        invoices: {
          id: number;
          invoice_number: string;
          customer_name: string;
          amount: string;
          currency: string;
          status: string;
        }[];
        payroll: {
          id: number;
          pay_period: string;
          employee_count: number;
          total_amount: string;
          currency: string;
          status: string;
        }[];
        expenses: {
          id: number;
          claimant_name: string;
          description: string;
          amount: string;
          currency: string;
          evidence_reference: string;
          status: string;
        }[];
      }
    | undefined;
  const profile = business?.profile;
  const invoices = business?.invoices ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 6 · BUSINESS"
        title="Business workspace"
        copy="Set up an organization profile and issue invoices after operations activates it."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      {!profile && !query.isLoading && (
        <form
          className="panel form-stack"
          onSubmit={submit(
            (d) =>
              api("/business/organizations", {
                method: "POST",
                body: JSON.stringify({ legal_name: d.get("legal_name") }),
              }),
            "Business profile created and sent for review.",
          )}
        >
          <h3>Create business profile</h3>
          <label>
            Legal name
            <input name="legal_name" required minLength={2} />
          </label>
          <button disabled={working}>Submit profile</button>
        </form>
      )}
      {profile && (
        <div className="panel">
          <h3>{profile.legal_name}</h3>
          <StatePill value={profile.status} />
        </div>
      )}
      {profile?.status === "active" && (
        <>
          <div className="two-column">
            <form
              className="panel form-stack"
              onSubmit={submit(
                (d) =>
                  api("/business/invoices", {
                    method: "POST",
                    body: JSON.stringify({
                      customer_name: d.get("customer_name"),
                      amount: d.get("amount"),
                      currency: d.get("currency"),
                    }),
                  }),
                "Invoice issued.",
              )}
            >
              <h3>Issue invoice</h3>
              <label>
                Customer name
                <input name="customer_name" required />
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
                Currency
                <select name="currency">
                  <option>PKR</option>
                  <option>USD</option>
                  <option>EUR</option>
                </select>
              </label>
              <button disabled={working}>Create invoice</button>
            </form>
            <div className="panel">
              <h3>Invoices</h3>
              {invoices.length ? (
                invoices.map((invoice) => (
                  <div className="beneficiary-row" key={invoice.id}>
                    <span>
                      <b>{invoice.invoice_number}</b>
                      <small>
                        {invoice.customer_name} ·{" "}
                        {money(invoice.amount, invoice.currency)}
                      </small>
                    </span>
                    <StatePill value={invoice.status} />
                    {invoice.status === "issued" && (
                      <button
                        disabled={working}
                        onClick={() =>
                          void perform(
                            () =>
                              api(`/business/invoices/${invoice.id}/status`, {
                                method: "PATCH",
                                body: JSON.stringify({ status: "paid" }),
                              }),
                            "Invoice marked paid in demo.",
                          )
                        }
                      >
                        Mark paid (demo)
                      </button>
                    )}
                    {invoice.status === "paid" && (
                      <button
                        disabled={working}
                        onClick={() =>
                          void perform(
                            () =>
                              api(`/business/invoices/${invoice.id}/status`, {
                                method: "PATCH",
                                body: JSON.stringify({ status: "refunded" }),
                              }),
                            "Invoice refunded in demo.",
                          )
                        }
                      >
                        Refund (demo)
                      </button>
                    )}
                  </div>
                ))
              ) : (
                <Empty text="No invoices issued yet." />
              )}
            </div>
          </div>
          <div className="two-column">
            <form
              className="panel form-stack"
              onSubmit={submit(
                (d) =>
                  api("/business/payroll", {
                    method: "POST",
                    body: JSON.stringify({
                      pay_period: d.get("pay_period"),
                      employee_count: Number(d.get("employee_count")),
                      total_amount: d.get("total_amount"),
                      currency: d.get("payroll_currency"),
                    }),
                  }),
                "Payroll batch sent for approval.",
              )}
            >
              <h3>Prepare payroll batch</h3>
              <label>
                Pay period
                <input name="pay_period" type="month" required />
              </label>
              <label>
                Employees
                <input name="employee_count" type="number" min="1" required />
              </label>
              <label>
                Total amount
                <input
                  name="total_amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                />
              </label>
              <label>
                Currency
                <select name="payroll_currency">
                  <option>PKR</option>
                  <option>USD</option>
                  <option>EUR</option>
                </select>
              </label>
              <button disabled={working}>Submit for approval</button>
              <p className="form-hint">
                Approval workflow only; payroll is not transferred.
              </p>
            </form>
            <div className="panel">
              <h3>Payroll batches</h3>
              {business?.payroll?.length ? (
                business.payroll.map((batch) => (
                  <div className="beneficiary-row" key={batch.id}>
                    <span>
                      <b>{batch.pay_period}</b>
                      <small>
                        {batch.employee_count} employees ·{" "}
                        {money(batch.total_amount, batch.currency)}
                      </small>
                    </span>
                    <StatePill value={batch.status} />
                  </div>
                ))
              ) : (
                <Empty text="No payroll batches." />
              )}
            </div>
          </div>
          <div className="two-column">
            <form
              className="panel form-stack"
              onSubmit={submit(
                (d) =>
                  api("/business/expenses", {
                    method: "POST",
                    body: JSON.stringify({
                      claimant_name: d.get("claimant_name"),
                      description: d.get("description"),
                      amount: d.get("expense_amount"),
                      currency: d.get("expense_currency"),
                      evidence_reference: d.get("evidence_reference"),
                    }),
                  }),
                "Expense claim submitted.",
              )}
            >
              <h3>Submit expense claim</h3>
              <label>
                Employee
                <input name="claimant_name" required />
              </label>
              <label>
                Description
                <input name="description" required />
              </label>
              <label>
                Amount
                <input
                  name="expense_amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                />
              </label>
              <label>
                Receipt reference
                <input name="evidence_reference" />
              </label>
              <label>
                Currency
                <select name="expense_currency">
                  <option>PKR</option>
                  <option>USD</option>
                  <option>EUR</option>
                </select>
              </label>
              <button disabled={working}>Send for approval</button>
            </form>
            <div className="panel">
              <h3>Expense claims</h3>
              {business?.expenses?.length ? (
                business.expenses.map((claim) => (
                  <div className="beneficiary-row" key={claim.id}>
                    <span>
                      <b>{claim.description}</b>
                      <small>
                        {claim.claimant_name} ·{" "}
                        {money(claim.amount, claim.currency)} ·{" "}
                        {claim.evidence_reference || "no receipt ref"}
                      </small>
                    </span>
                    <StatePill value={claim.status} />
                  </div>
                ))
              ) : (
                <Empty text="No expense claims." />
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
