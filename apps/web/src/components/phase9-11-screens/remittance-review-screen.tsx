"use client";

import { api, money } from "@/lib/api";
import { Empty, PageTitle } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

export function RemittanceReviewScreen(props: Phase911ScreenProps) {
  const { query, busy, notice, act } = props;
  const rows =
    (query.data as
      | {
          id: number;
          destination_country: string;
          source_amount: string;
          source_currency: string;
          destination_amount: string;
          destination_currency: string;
          status: string;
        }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS · REMITTANCE"
        title="Remittance review queue"
        copy="Review demo requests. Approval records a status only."
      />
      {notice}
      <div className="panel">
        {rows.filter((row) => row.status === "pending_review").length ? (
          rows
            .filter((row) => row.status === "pending_review")
            .map((row) => (
              <div className="beneficiary-row" key={row.id}>
                <span>
                  <b>
                    {row.destination_country} ·{" "}
                    {money(row.source_amount, row.source_currency)}
                  </b>
                  <small>
                    Recipient amount{" "}
                    {money(row.destination_amount, row.destination_currency)}
                  </small>
                </span>
                <div className="inline-actions">
                  <button
                    disabled={busy}
                    onClick={() =>
                      void act(
                        () =>
                          api(`/remittances/${row.id}`, {
                            method: "PATCH",
                            body: JSON.stringify({ decision: "approved" }),
                          }),
                        "Remittance approved.",
                      )
                    }
                  >
                    Approve
                  </button>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void act(
                        () =>
                          api(`/remittances/${row.id}`, {
                            method: "PATCH",
                            body: JSON.stringify({ decision: "rejected" }),
                          }),
                        "Remittance rejected.",
                      )
                    }
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))
        ) : (
          <Empty text="No remittances await review." />
        )}
      </div>
    </>
  );
}
