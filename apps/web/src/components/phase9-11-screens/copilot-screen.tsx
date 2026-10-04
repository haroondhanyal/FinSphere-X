"use client";

import { api } from "@/lib/api";
import { PageTitle } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

export function CopilotScreen(props: Phase911ScreenProps) {
  const { busy, result, notice, form } = props;
  const status = props.query.data as
    | { ai_enabled: boolean; model: string | null }
    | undefined;
  const requireConsent = (data: FormData) => {
    if (!data.get("ai_consent")) {
      throw new Error("Confirm the data-sharing notice before generating assistance.");
    }
  };
  const consent = (text: string) => (
    <label className="checkbox-row">
      <input name="ai_consent" type="checkbox" required />
      {text}
    </label>
  );

  return (
    <>
      <PageTitle
        eyebrow="PHASE 10 · AI COPILOT"
        title="Explain, summarize, forecast"
        copy="AI-assisted explanations and extraction with a local fallback. Outputs require human review."
      />
      {notice}
      <div className="panel form-hint" role="status">
        {status?.ai_enabled
          ? `AI provider enabled (${status.model}). Submitted source text and limited transaction details may be sent to OpenAI. Do not submit information without authorization.`
          : "AI provider is not configured. These tools use local fallback behavior. Add OPENAI_API_KEY to the API environment to enable model assistance."}
      </div>
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={form(
            (data) => {
              requireConsent(data);
              return api(`/copilot/transactions/${data.get("transaction_id")}/explanation`, {
                method: "POST",
                body: JSON.stringify({ consent: true }),
              });
            },
            "Transaction explanation generated.",
          )}
        >
          <h3>Explain transaction</h3>
          <label>
            Transaction ID
            <input name="transaction_id" type="number" min="1" required />
          </label>
          {consent("I understand limited transaction details may be processed by the configured AI provider.")}
          <button disabled={busy}>Explain</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (data) => {
              requireConsent(data);
              return api("/copilot/summarize", {
                method: "POST",
                body: JSON.stringify({ source_text: data.get("source_text"), consent: true }),
              });
            },
            "Source summary generated.",
          )}
        >
          <h3>Summarize source</h3>
          <label>
            Text
            <textarea name="source_text" minLength={3} maxLength={12000} required />
          </label>
          {consent("I am authorized to submit this text for AI processing.")}
          <button disabled={busy}>Summarize</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (data) => {
              requireConsent(data);
              return api("/copilot/documents/extract", {
                method: "POST",
                body: JSON.stringify({
                  document_type: data.get("document_type"),
                  document_text: data.get("document_text"),
                  consent: true,
                }),
              });
            },
            "Document candidates extracted.",
          )}
        >
          <h3>Document extraction</h3>
          <label>
            Document type
            <input name="document_type" required />
          </label>
          <label>
            Document text
            <textarea name="document_text" minLength={3} maxLength={12000} required />
          </label>
          {consent("I am authorized to submit this document text for AI processing.")}
          <button disabled={busy}>Extract candidates</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (data) => {
              requireConsent(data);
              const file = data.get("document_file");
              if (!(file instanceof File)) throw new Error("Choose a PDF or image file.");
              const payload = new FormData();
              payload.set("document_type", String(data.get("upload_document_type") || "document"));
              payload.set("consent", "true");
              payload.set("file", file);
              return api("/copilot/documents/extract-upload", { method: "POST", body: payload });
            },
            "Document candidates extracted.",
          )}
        >
          <h3>Extract from PDF or image</h3>
          <label>
            Document type
            <input name="upload_document_type" defaultValue="financial document" required />
          </label>
          <label>
            PDF or image
            <input name="document_file" type="file" accept="application/pdf,image/png,image/jpeg,image/webp" required />
          </label>
          <p className="form-hint">Maximum 6 MB. The file is processed in memory and sent to the configured OpenAI provider; it is not saved by this app.</p>
          {consent("I am authorized to send this file to the configured AI provider for extraction.")}
          <button disabled={busy}>Extract candidates</button>
        </form>
        <form
          className="panel form-stack"
          onSubmit={form(
            (data) => {
              requireConsent(data);
              return api("/copilot/forecast", {
                method: "POST",
                body: JSON.stringify({ consent: true }),
              });
            },
            "Forecast summary calculated.",
          )}
        >
          <h3>Transaction trend</h3>
          <p className="form-hint">
            The app calculates a historical average. AI can explain the result; it does not make a decision.
          </p>
          {consent("I understand limited transaction aggregates may be processed by the configured AI provider.")}
          <button disabled={busy}>Calculate summary</button>
        </form>
      </div>
      {result && <pre className="panel">{JSON.stringify(result, null, 2)}</pre>}
    </>
  );
}
