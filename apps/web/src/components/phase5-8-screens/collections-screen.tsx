"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function CollectionsScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform } = props;
  const data = query.data as
    | {
        loans: {
          id: number;
          loan_id: number;
          installment_number: number;
          due_at: string;
          amount: string;
          status: string;
        }[];
        bnpl: {
          id: number;
          plan_id: number;
          installment_number: number;
          due_at: string;
          amount: string;
          status: string;
        }[];
      }
    | undefined;
  const rows = [
    ...(data?.loans.map((row) => ({ ...row, kind: "loan" })) ?? []),
    ...(data?.bnpl.map((row) => ({ ...row, kind: "BNPL" })) ?? []),
  ];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 5 · COLLECTIONS"
        title="Collections queue"
        copy="Track due loan and BNPL installments. Recording payment only updates demo status."
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
            <div className="beneficiary-row" key={`${row.kind}-${row.id}`}>
              <span>
                <b>
                  {row.kind} installment #{row.installment_number}
                </b>
                <small>
                  Due {new Date(row.due_at).toLocaleDateString()} ·{" "}
                  {money(row.amount)}
                </small>
              </span>
              <StatePill value={row.status} />
              <button
                disabled={working}
                onClick={() =>
                  void perform(
                    () =>
                      api(
                        row.kind === "loan"
                          ? `/loans/collections/${row.id}/record-payment`
                          : `/bnpl/installments/${row.id}/record-payment`,
                        { method: "POST" },
                      ),
                    "Demo payment recorded; no funds moved.",
                  )
                }
              >
                Record demo payment
              </button>
            </div>
          ))
        ) : (
          <Empty text="No installment collections are pending." />
        )}
      </div>
    </>
  );
}
