"use client";

import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function SettlementReviewScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform } = props;
  const settlements =
    (query.data as
      | {
          id: number;
          organization_id: number;
          reference: string;
          gross_amount: string;
          fee_amount: string;
          net_amount: string;
          currency: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS · SETTLEMENTS"
        title="Settlement review"
        copy="Verify simulated settlement totals. Review does not move funds."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        {settlements.length ? (
          settlements.map((row) => (
            <div className="beneficiary-row" key={row.id}>
              <span>
                <b>
                  {row.reference} · organization #{row.organization_id}
                </b>
                <small>
                  Gross {money(row.gross_amount, row.currency)} · fee{" "}
                  {money(row.fee_amount, row.currency)} · net{" "}
                  {money(row.net_amount, row.currency)}
                </small>
              </span>
              <div className="inline-actions">
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/merchant/settlements/${row.id}/review`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "matched" }),
                        }),
                      "Settlement marked matched.",
                    )
                  }
                >
                  Mark matched
                </button>
                <button
                  disabled={working}
                  onClick={() =>
                    void perform(
                      () =>
                        api(`/merchant/settlements/${row.id}/review`, {
                          method: "PATCH",
                          body: JSON.stringify({ decision: "exception" }),
                        }),
                      "Settlement flagged as exception.",
                    )
                  }
                >
                  Flag exception
                </button>
              </div>
            </div>
          ))
        ) : (
          <Empty text="No simulated settlement runs need review." />
        )}
      </div>
    </>
  );
}
