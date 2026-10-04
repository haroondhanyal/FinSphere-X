"use client";

import { api } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import type { KycCase } from "./domain-types";
import type { Phase58ScreenProps } from "./types";

export function RiskCaseworkScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const riskData = query.data as
    | {
        cases: KycCase[];
        screenings: {
          id: number;
          subject_name: string;
          category: string;
          score: number;
          result: string;
          rationale: string;
        }[];
      }
    | undefined;
  const cases = riskData?.cases ?? [];
  const screenings = riskData?.screenings ?? [];
  return (
    <>
      <PageTitle
        eyebrow="PHASE 8 · RISK & COMPLIANCE"
        title="Risk casework"
        copy="Record cases and run a clearly labeled mock screening fixture. Human review is required."
      />
      <Notice
        error={
          error || (query.error instanceof Error ? query.error.message : "")
        }
        success={notice}
      />
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={submit(
            (d) =>
              api("/risk/screenings", {
                method: "POST",
                body: JSON.stringify({
                  subject_name: d.get("subject_name"),
                  category: d.get("screening_category"),
                }),
              }),
            "Mock screening recorded; review the result manually.",
          )}
        >
          <h3>Mock screening</h3>
          <label>
            Subject name
            <input name="subject_name" minLength={2} required />
          </label>
          <label>
            Screening type
            <select name="screening_category">
              <option>sanctions</option>
              <option>pep</option>
              <option>adverse_media</option>
            </select>
          </label>
          <button disabled={working}>Run mock screening</button>
          <p className="form-hint">
            Synthetic keyword fixture only; this is not a compliance result.
          </p>
        </form>
        <div className="panel">
          <h3>Screening results</h3>
          {screenings.length ? (
            screenings.map((item) => (
              <div className="beneficiary-row" key={item.id}>
                <span>
                  <b>
                    {item.subject_name} · {item.category}
                  </b>
                  <small>
                    {item.rationale} · score {item.score}
                  </small>
                </span>
                <StatePill value={item.result} />
              </div>
            ))
          ) : (
            <Empty text="No mock screening runs." />
          )}
        </div>
      </div>
      <form
        className="panel form-stack"
        onSubmit={submit(
          (d) =>
            api("/risk/cases", {
              method: "POST",
              body: JSON.stringify({
                customer_id: Number(d.get("customer_id")),
                category: d.get("category"),
                summary: d.get("summary"),
                score: Number(d.get("score")),
              }),
            }),
          "Risk case created.",
        )}
      >
        <h3>Open case</h3>
        <label>
          Customer ID
          <input name="customer_id" type="number" min="1" required />
        </label>
        <label>
          Category
          <select name="category">
            <option>fraud</option>
            <option>aml</option>
            <option>sanctions</option>
          </select>
        </label>
        <label>
          Summary
          <input name="summary" required minLength={8} />
        </label>
        <label>
          Risk score (simulated)
          <input name="score" type="number" min="0" max="100" required />
        </label>
        <button disabled={working}>Create case</button>
      </form>
      <form
        className="panel form-stack"
        onSubmit={submit(async (d) => {
          const id = d.get("case_id");
          const note = String(d.get("note") || "");
          const evidence = String(d.get("evidence_reference") || "");
          if (note)
            await api(`/risk/cases/${id}/notes`, {
              method: "POST",
              body: JSON.stringify({ note }),
            });
          if (evidence)
            await api(`/risk/cases/${id}/evidence`, {
              method: "POST",
              body: JSON.stringify({ evidence_reference: evidence }),
            });
        }, "Case note/evidence recorded.")}
      >
        <h3>Add case note or evidence</h3>
        <label>
          Case ID
          <input name="case_id" type="number" min="1" required />
        </label>
        <label>
          Note
          <input name="note" />
        </label>
        <label>
          Evidence reference
          <input name="evidence_reference" />
        </label>
        <button disabled={working}>Save case material</button>
      </form>
      <div className="panel">
        <h3>Cases</h3>
        {cases.length ? (
          cases.map((item) => (
            <div className="beneficiary-row" key={item.id}>
              <span>
                <b>
                  {item.category} · customer #{item.customer_id}
                </b>
                <small>
                  {item.summary} · simulated score {item.score}
                </small>
                {item.notes ? <small>Notes: {item.notes}</small> : null}
                {item.evidence_reference ? (
                  <small>Evidence: {item.evidence_reference}</small>
                ) : null}
              </span>
              <StatePill value={item.status} />
              {item.status === "open" && (
                <div className="inline-actions">
                  {["cleared", "escalated", "reported", "false_positive"].map(
                    (decision) => (
                      <button
                        key={decision}
                        disabled={working}
                        onClick={() =>
                          void perform(
                            () =>
                              api(`/risk/cases/${item.id}`, {
                                method: "PATCH",
                                body: JSON.stringify({ decision }),
                              }),
                            `Case ${decision.replaceAll("_", " ")}.`,
                          )
                        }
                      >
                        {decision.replaceAll("_", " ")}
                      </button>
                    ),
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <Empty text="No risk cases are open." />
        )}
      </div>
    </>
  );
}
