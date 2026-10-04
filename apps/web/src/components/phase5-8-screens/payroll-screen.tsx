"use client";

import { money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function PayrollScreen(props: Phase58ScreenProps) {
  const { query, error, notice } = props;
  const batches =
    (query.data as
      | {
          id: number;
          pay_period: string;
          employee_count: number;
          total_amount: string;
          currency: string;
          status: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 6 · PAYROLL"
        title="Payroll batches"
        copy="Submit payroll totals for maker-checker review. No funds are transferred."
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
    </>
  );
}
