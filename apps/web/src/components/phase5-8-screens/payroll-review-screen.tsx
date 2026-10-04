"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function PayrollReviewScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform } = props;
  const batches =
    (query.data as
      | {
          id: number;
          organization_id: number;
          pay_period: string;
          employee_count: number;
          total_amount: string;
          currency: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS · MAKER CHECKER"
        title="Payroll approval queue"
        copy="Review submitted totals and record an approval decision."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        {batches.length ? (
          batches.map((batch) => (
            <div className="beneficiary-row" key={batch.id}>
              <span>
                <b>
                  {batch.pay_period} · organization #{batch.organization_id}
                </b>
                <small>
                  {batch.employee_count} employees ·{" "}
                  {money(batch.total_amount, batch.currency)}
                </small>
              </span>
              <div className="inline-actions">
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/business/payroll/${batch.id}`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "approved" }),
                        }),
                      "Payroll batch approved.",
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
                        api(`/business/payroll/${batch.id}`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "rejected" }),
                        }),
                      "Payroll batch rejected.",
                    )
                  }
                >
                  Reject
                </button>
              </div>
            </div>
          ))
        ) : (
          <Empty text="No payroll batches are awaiting review." />
        )}
      </div>
    </>
  );
}
