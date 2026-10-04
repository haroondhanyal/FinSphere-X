"use client";

import { api } from "@/lib/api";
import { Empty, PageTitle, StatePill } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

type Consent = {
  id: number;
  provider_name: string;
  scopes: string[];
  status: string;
  expires_at: string;
};

export function OpenBankingScreen(props: Phase911ScreenProps) {
  const { query, busy, notice, form, act } = props;
  const data = query.data as
    | {
        providers: { id: string; name: string; status: string }[];
        consents: Consent[];
      }
    | undefined;
  return (
    <>
      <PageTitle
        eyebrow="PHASE 11 · OPEN BANKING"
        title="Consent management"
        copy="Grant and revoke local sandbox data-sharing scopes."
      />
      {notice}
      <form
        className="panel form-stack"
        onSubmit={form(
          (d) =>
            api("/open-banking/consents", {
              method: "POST",
              body: JSON.stringify({
                provider_name: d.get("provider_name"),
                scopes: ["accounts:read", "balances:read"],
                duration_days: Number(d.get("duration_days")),
              }),
            }),
          "Sandbox consent created.",
        )}
      >
        <h3>New consent</h3>
        <label>
          Sandbox provider
          <select name="provider_name">
            {data?.providers.map((provider) => (
              <option key={provider.id}>{provider.name}</option>
            ))}
          </select>
        </label>
        <label>
          Duration in days
          <input
            name="duration_days"
            type="number"
            min="1"
            max="365"
            defaultValue="90"
          />
        </label>
        <button disabled={busy}>Grant consent</button>
      </form>
      <div className="panel">
        {data?.consents.length ? (
          data.consents.map((consent) => (
            <div className="beneficiary-row" key={consent.id}>
              <span>
                <b>{consent.provider_name}</b>
                <small>
                  {consent.scopes.join(", ")} · expires{" "}
                  {new Date(consent.expires_at).toLocaleDateString()}
                </small>
              </span>
              <StatePill value={consent.status} />
              {consent.status === "active" && (
                <button
                  disabled={busy}
                  onClick={() =>
                    void act(
                      () =>
                        api(`/open-banking/consents/${consent.id}/revoke`, {
                          method: "POST",
                        }),
                      "Consent revoked.",
                    )
                  }
                >
                  Revoke
                </button>
              )}
            </div>
          ))
        ) : (
          <Empty text="No consents recorded." />
        )}
      </div>
      <p className="form-hint">
        No external open banking provider is contacted.
      </p>
    </>
  );
}
