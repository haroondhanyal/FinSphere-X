"use client";

import { api } from "@/lib/api";
import { Empty, Notice, PageTitle } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function BusinessReviewScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform } = props;
  const organizations =
    (query.data as
      | { id: number; user_id: number; legal_name: string; status: string }[]
      | undefined) ?? [];
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS · BUSINESS ONBOARDING"
        title="Business review"
        copy="Approve or reject pending organization profiles."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="panel">
        {organizations.filter((row) => row.status === "pending_review")
          .length ? (
          organizations
            .filter((row) => row.status === "pending_review")
            .map((row) => (
              <div className="beneficiary-row" key={row.id}>
                <span>
                  <b>{row.legal_name}</b>
                  <small>
                    Organization #{row.id} · owner #{row.user_id}
                  </small>
                </span>
                <div className="inline-actions">
                  <button
                    disabled={working}
                    onClick={() =>
                      void perform(
                        () =>
                          api(`/business/organizations/${row.id}`, {
                            method: "PATCH",
                            body: JSON.stringify({ decision: "active" }),
                          }),
                        "Business profile approved.",
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
                          api(`/business/organizations/${row.id}`, {
                            method: "PATCH",
                            body: JSON.stringify({ decision: "rejected" }),
                          }),
                        "Business profile rejected.",
                      )
                    }
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))
        ) : (
          <Empty text="No business profiles are waiting for review." />
        )}
      </div>
    </>
  );
}
