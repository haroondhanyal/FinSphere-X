"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function ExpenseReviewScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform } = props;
  const rows =
    (query.data as
      | {
          id: number;
          organization_id: number;
          claimant_name: string;
          description: string;
          amount: string;
          currency: string;
          evidence_reference: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS · EXPENSES"
        title="Expense approval queue"
        copy="Review receipt references and record a maker-checker decision."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        {rows.length ? (
          rows.map((row) => (
            <div className="beneficiary-row" key={row.id}>
              <span>
                <b>
                  {row.description} · {row.claimant_name}
                </b>
                <small>
                  Org #{row.organization_id} · {money(row.amount, row.currency)}{" "}
                  · {row.evidence_reference || "no evidence reference"}
                </small>
              </span>
              <div className="inline-actions">
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/business/expenses/${row.id}`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "approved" }),
                        }),
                      "Expense claim approved.",
                    )
                  }
                >
                  Approve
                </button>
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/business/expenses/${row.id}`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "rejected" }),
                        }),
                      "Expense claim rejected.",
                    )
                  }
                >
                  Reject
                </button>
              </div>
            </div>
          ))
        ) : (
          <Empty text="No expense claims awaiting review." />
        )}
      </div>
    </>
  );
}
