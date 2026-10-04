"use client";

import { api } from "@/lib/api";
import { Empty, PageTitle, StatePill } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

export function DeveloperPlatformScreen(props: Phase911ScreenProps) {
  const { query, busy, result, notice, form, act } = props;
  const data = query.data as
    | {
        clients: Record<string, unknown>[];
        webhooks: Record<string, unknown>[];
        deliveries: Record<string, unknown>[];
      }
    | undefined;
  return (
    <>
      <PageTitle
        eyebrow="PHASE 11 · DEVELOPER PLATFORM"
        title="API clients and webhooks"
        copy="Create read-only sandbox credentials, configure event URLs, and inspect local delivery logs."
      />
      {notice}
      <div className="two-column">
        <div className="panel form-stack">
          <h3>Sandbox API access</h3>
          <p className="form-hint">Generated keys authenticate the read-only routes `/api/v1/developer/v1/me`, `/accounts`, and `/transactions`. They cannot authorize money movement.</p>
        </div>
        <form
          className="panel form-stack"
          onSubmit={form(
            (d) =>
              api("/developer/clients", {
                method: "POST",
                body: JSON.stringify({ name: d.get("name") }),
              }),
            "Sandbox API key generated.",
          )}
        >
          <h3>Create API client</h3>
          <label>
            Client name
            <input name="name" required />
          </label>
          <button disabled={busy}>Create key</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (d) =>
              api("/developer/webhooks", {
                method: "POST",
                body: JSON.stringify({
                  url: d.get("url"),
                  event_types: ["transaction.posted", "account.updated"],
                }),
              }),
            "Webhook endpoint saved.",
          )}
        >
          <h3>Register webhook</h3>
          <label>
            HTTPS URL
            <input
              name="url"
              type="url"
              placeholder="https://example.test/hooks"
              required
            />
          </label>
          <button disabled={busy}>Register endpoint</button>
        </form>
      </div>
      {result && <pre className="panel">{JSON.stringify(result, null, 2)}</pre>}
      <div className="panel">
        <h3>API clients</h3>
        {data?.clients.map((client) => (
          <div className="beneficiary-row" key={String(client.id)}>
            <span>
              <b>{String(client.name)}</b>
              <small>{String(client.key_prefix)}</small>
            </span>
            <StatePill value={Boolean(client.active) ? "active" : "revoked"} />
            {Boolean(client.active) && (
              <button
                disabled={busy}
                onClick={() =>
                  void act(
                    () =>
                      api(`/developer/clients/${String(client.id)}/revoke`, {
                        method: "POST",
                      }),
                    "API client revoked.",
                  )
                }
              >
                Revoke
              </button>
            )}
          </div>
        ))}
      </div>
      <div className="panel">
        <h3>Webhooks and sandbox deliveries</h3>
        {data?.webhooks.map((endpoint) => (
          <div className="beneficiary-row" key={String(endpoint.id)}>
            <span>
              <b>{String(endpoint.url)}</b>
              <small>{JSON.stringify(endpoint.event_types)}</small>
            </span>
            <button
              disabled={busy}
              onClick={() =>
                void act(
                  () =>
                    api(
                      `/developer/webhooks/${String(endpoint.id)}/test-delivery`,
                      { method: "POST" },
                    ),
                  "Sandbox delivery queued.",
                )
              }
            >
              Queue test event
            </button>
          </div>
        ))}
        {data?.deliveries.map((delivery, index) => (
          <div
            className="beneficiary-row"
            key={`delivery-${String(delivery.id ?? index)}`}
          >
            <span>
              <b>{String(delivery.event_type)}</b>
              <small>{JSON.stringify(delivery.payload)}</small>
            </span>
            <StatePill value={String(delivery.status)} />
          </div>
        ))}
        {!data?.webhooks.length && <Empty text="No endpoints configured." />}
      </div>
      <p className="form-hint">
        API keys and webhook signing secrets are shown once; sandbox events are
        never sent to the target URL.
      </p>
    </>
  );
}
