"use client";

import { money } from "@/lib/api";
import { Notice, PageTitle } from "../screen-primitives";
import type { Phase58ScreenProps } from "./types";

export function RoleDashboardScreen(props: Phase58ScreenProps) {
  const { section, query, error } = props;
  const summary = query.data as Record<string, string | number> | undefined;
  const disclosure =
    typeof summary?.disclosure === "string" ? summary.disclosure : "";
  const heading = section.startsWith("business")
    ? "Business overview"
    : section.startsWith("merchant")
      ? "Merchant overview"
      : "Operations overview";
  return (
    <>
      <PageTitle
        eyebrow="ROLE WORKSPACE"
        title={heading}
        copy="A summary of your current local demo work queues and records."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
      />
      {query.isLoading ? (
        <div className="panel">
          <p className="muted">Loading overview…</p>
        </div>
      ) : (
        <div className="panel-grid">
          {Object.entries(summary ?? {})
            .filter(
              ([key, value]) =>
                key !== "disclosure" &&
                key !== "organization" &&
                key !== "currency" &&
                (typeof value === "string" || typeof value === "number"),
            )
            .map(([key, value]) => (
              <div className="panel" key={key}>
                <span className="eyebrow">
                  {key.replaceAll("_", " ").toUpperCase()}
                </span>
                <h3>
                  {typeof value === "string" && /^\d+(\.\d+)?$/.test(value)
                    ? money(value, String(summary?.currency ?? "PKR"))
                    : value}
                </h3>
              </div>
            ))}
        </div>
      )}
      {disclosure ? <p className="form-hint">{disclosure}</p> : null}
    </>
  );
}
