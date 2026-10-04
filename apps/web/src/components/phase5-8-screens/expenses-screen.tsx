"use client";

import { money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function ExpensesScreen(props: Phase58ScreenProps) {
  const { query, error, notice } = props;
  const rows =
    (query.data as
      | {
          id: number;
          claimant_name: string;
          description: string;
          amount: string;
          currency: string;
          evidence_reference: string;
          status: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 6 · EXPENSES"
        title="Expense claims"
        copy="Track employee reimbursement claims and receipt references."
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
                  {money(row.amount, row.currency)} · evidence:{" "}
                  {row.evidence_reference || "none"}
                </small>
              </span>
              <StatePill value={row.status} />
            </div>
          ))
        ) : (
          <Empty text="No expense claims." />
        )}
      </div>
    </>
  );
}
