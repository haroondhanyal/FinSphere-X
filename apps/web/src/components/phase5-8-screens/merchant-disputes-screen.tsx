"use client";

import { useState } from "react";
import { api, money } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import { ModuleDataTable, ModuleRecordToolbar } from "../module-data-table";
import type { Phase58ScreenProps } from "./types";

type Dispute = {
  id: number;
  sale_id: number;
  sale_reference: string;
  sale_description: string;
  sale_amount: string;
  currency: string;
  organization_id: number;
  reason: string;
  evidence_reference: string;
  status: string;
  decision: string;
  decision_note: string;
  created_at: string;
};
type DisputeData = {
  items: Dispute[];
  can_review: boolean;
  available_sales: { id: number; reference: string; description: string; amount: string; currency: string }[];
};
const emptyDisputes: Dispute[] = [];

export function MerchantDisputesScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const data = query.data as DisputeData | undefined;
  const rows = data?.items ?? emptyDisputes;
  const isStaff = Boolean(data?.can_review);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selected, setSelected] = useState<Dispute | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const filtered = rows.filter((row) =>
    (statusFilter === "all" || row.status === statusFilter) &&
    `#${row.id} ${row.sale_reference} ${row.reason} ${row.evidence_reference}`.toLowerCase().includes(search.trim().toLowerCase()),
  );
  const count = (status: string) => rows.filter((row) => row.status === status).length;

  async function decide(decision: "resolved" | "escalated") {
    if (!selected || reviewNote.trim().length < 5) return;
    const saved = await perform(() => api(`/merchant/disputes/${selected.id}`, {
      method: "PATCH", body: JSON.stringify({ decision, note: reviewNote.trim() }),
    }), `Dispute #${selected.id} ${decision} with reviewer notes.`);
    if (saved) { setSelected(null); setReviewNote(""); }
  }

  return <>
    <PageTitle eyebrow="OPERATIONS WORKSPACE · DISPUTES" title="Disputes & chargebacks" copy="Investigate merchant cases, review evidence and record a reasoned resolution or escalation." />
    <Notice error={error || (query.error instanceof Error ? query.error.message : "")} success={notice} />
    <div className="module-summary-grid dispute-summary">
      <div><span>Total cases</span><b>{rows.length}</b></div>
      <div><span>Open</span><b>{count("open")}</b></div>
      <div><span>Resolved</span><b>{count("resolved")}</b></div>
      <div><span>Escalated</span><b>{count("escalated")}</b></div>
    </div>
    {data && !isStaff && <section className="panel dispute-open-panel">
      <div><span className="eyebrow">MERCHANT ACTION</span><h3>Open a dispute</h3><p className="muted">Select one of your recorded sales and attach the reason and evidence reference.</p></div>
      {data?.available_sales.length ? <form className="form-stack dispute-create-form" onSubmit={submit((form) => api("/merchant/disputes", {
        method: "POST", body: JSON.stringify({ sale_id: Number(form.get("sale_id")), reason: form.get("reason"), evidence_reference: form.get("evidence_reference") }),
      }), "Dispute opened and added to the review queue.")}>
        <label>Sale<select name="sale_id" required defaultValue=""><option value="" disabled>Choose a sale</option>{data.available_sales.map((sale) => <option key={sale.id} value={sale.id}>{sale.reference} · {sale.description} · {money(sale.amount, sale.currency)}</option>)}</select></label>
        <label>Reason<textarea name="reason" rows={2} minLength={4} maxLength={240} required placeholder="Describe the issue with this sale" /></label>
        <label>Evidence reference<input name="evidence_reference" maxLength={240} placeholder="File reference or evidence URL" /></label>
        <button className="button primary" disabled={working}>Submit dispute</button>
      </form> : <Empty text="Record a sale before opening a dispute." />}
    </section>}
    <div className="module-list-heading"><div><span className="eyebrow">CASE REGISTER</span><h3>{isStaff ? "All merchant cases" : "Your disputes"}</h3></div><span>{filtered.length} of {rows.length}</span></div>
    <ModuleRecordToolbar search={search} onSearch={setSearch} placeholder="Search case, sale or reason" filter={statusFilter} onFilter={setStatusFilter} options={[{value:"all",label:"All statuses"},{value:"open",label:"Open"},{value:"resolved",label:"Resolved"},{value:"escalated",label:"Escalated"}]} />
    {query.isLoading ? <div className="panel"><p className="muted">Loading dispute register…</p></div> : <ModuleDataTable rows={filtered} empty="No disputes match these filters." columns={[
      {key:"case",label:"Case",render:(row) => <><b>DIS-{String(row.id).padStart(5,"0")}</b><small className="member-email">{new Date(row.created_at).toLocaleDateString()}</small></>},
      {key:"sale",label:"Sale",render:(row) => <><b>{row.sale_reference}</b><small className="member-email">{row.sale_description} · {money(row.sale_amount,row.currency)}</small></>},
      {key:"reason",label:"Reason & evidence",render:(row) => <><b>{row.reason}</b><small className="member-email">{row.evidence_reference || "No evidence reference"}</small></>},
      {key:"status",label:"Status",render:(row) => <StatePill value={row.status} />},
      {key:"decision",label:"Review",render:(row) => isStaff && row.status === "open" ? <button type="button" className="button primary" onClick={() => { setSelected(row); setReviewNote(""); }}>Review case</button> : <span>{row.decision || "Awaiting review"}</span>},
    ]} />}

    {selected && <div className="review-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}>
      <section className="review-modal" role="dialog" aria-modal="true" aria-labelledby="dispute-review-title">
        <div className="review-modal-heading"><div><span className="eyebrow">DISPUTE CASE · DIS-{String(selected.id).padStart(5,"0")}</span><h2 id="dispute-review-title">{selected.reason}</h2></div><button className="review-close" type="button" onClick={() => setSelected(null)} aria-label="Close case">×</button></div>
        <div className="review-customer-grid">
          <div><small>Merchant organization</small><b>Organization #{selected.organization_id}</b></div>
          <div><small>Sale</small><b>{selected.sale_reference} · {selected.sale_description}</b></div>
          <div><small>Sale amount</small><b>{money(selected.sale_amount, selected.currency)}</b></div>
          <div><small>Evidence reference</small>{/^https?:\/\//i.test(selected.evidence_reference) ? <a href={selected.evidence_reference} target="_blank" rel="noreferrer">Open evidence ↗</a> : <b>{selected.evidence_reference || "None supplied"}</b>}</div>
          <div><small>Opened</small><b>{new Date(selected.created_at).toLocaleString()}</b></div>
          {selected.decision_note && <div><small>Previous reviewer note</small><b>{selected.decision_note}</b></div>}
        </div>
        <form className="stack-form review-decision-form" onSubmit={(event) => { event.preventDefault(); void decide("resolved"); }}>
          <label>Investigation notes<textarea value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} rows={4} minLength={5} maxLength={1000} required placeholder="Describe evidence checked and the reason for your decision." /></label>
          <div className="dispute-decision-actions">
            <button className="button primary" type="submit" disabled={working || reviewNote.trim().length < 5}>Resolve case</button>
            <button className="button dispute-escalate" type="button" disabled={working || reviewNote.trim().length < 5} onClick={(event) => {
              const form = event.currentTarget.form;
              if (form?.reportValidity()) void decide("escalated");
            }}>Escalate case</button>
          </div>
        </form>
      </section>
    </div>}
  </>;
}
