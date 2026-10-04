"use client";

import { useState, type FormEvent } from "react";
import Image from "next/image";
import { api, getAuthToken } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import { ModuleDataTable, ModuleRecordToolbar } from "../module-data-table";
import type { CustomerScreenProps } from "./types";

type ReviewDetail = {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  country: string;
  state: string;
  city: string;
  nationality: string;
  kyc_status: string;
  documents: { id: number; document_type: string; status: string; created_at: string }[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const decisions = ["approved", "rejected", "additional_information_required"] as const;

export function KycQueueScreen(props: CustomerScreenProps) {
  const { error, success, kycQueue, kycQueueQuery, run } = props;
  const [selected, setSelected] = useState<ReviewDetail | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [decision, setDecision] = useState<(typeof decisions)[number]>("approved");
  const [preview, setPreview] = useState<{ url: string; type: string; name: string } | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const visibleQueue = kycQueue.filter((customer) =>
    (statusFilter === "all" || customer.kyc_status === statusFilter) &&
    `${customer.full_name} ${customer.email ?? ""}`.toLowerCase().includes(search.trim().toLowerCase()),
  );
  const awaitingReview = kycQueue.filter((customer) => ["pending", "under_review", "additional_information_required"].includes(customer.kyc_status)).length;

  function closeReview() {
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setSelected(null);
    setDetailError("");
  }

  async function openReview(customerId: number) {
    setLoadingDetails(true);
    setDetailError("");
    setDecision("approved");
    try {
      const result = await api<ReviewDetail>(`/customers/${customerId}/kyc/review-details`);
      setSelected(result);
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "Could not load customer review details.");
    } finally {
      setLoadingDetails(false);
    }
  }

  async function viewDocument(documentId: number, name: string) {
    const token = getAuthToken();
    if (!token || !selected) return;
    setDetailError("");
    try {
      const response = await fetch(`${API_URL}/customers/${selected.id}/kyc/documents/${documentId}/view`, {
        headers: { Authorization: `Bearer ${token}` }, cache: "no-store",
      });
      if (!response.ok) throw new Error("Document could not be opened.");
      if (preview) URL.revokeObjectURL(preview.url);
      const blob = await response.blob();
      setPreview({ url: URL.createObjectURL(blob), type: blob.type, name });
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "Document could not be opened.");
    }
  }

  async function submitDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const reason = String(form.get("reason") ?? "").trim();
    if (decision !== "approved" && reason.length < 5) {
      setDetailError("Add a short reason before requesting more information or rejecting this case.");
      return;
    }
    const customerName = selected.full_name;
    await run(
      () => api(`/customers/${selected.id}/kyc/review`, {
        method: "POST", body: JSON.stringify({ decision, reason }),
      }),
      `${customerName}'s KYC marked ${decision.replaceAll("_", " ")}.`,
    );
    closeReview();
  }

  return (
    <>
      <PageTitle eyebrow="OPERATIONS WORKSPACE" title="KYC review queue" copy="Review customer details and identity documents before recording a decision." />
      <Notice error={error || kycQueueQuery.error?.message} success={success} />
      <div className="kyc-overview">
        <div><span>Awaiting review</span><b>{awaitingReview}</b></div>
        <div><span>Total customer records</span><b>{kycQueue.length}</b></div>
        <div><span>Documents submitted</span><b>{kycQueue.reduce((count, customer) => count + (customer.document_count ?? 0), 0)}</b></div>
      </div>
      <ModuleRecordToolbar search={search} onSearch={setSearch} placeholder="Search name or email" filter={statusFilter} onFilter={setStatusFilter} options={[{value:"all",label:"All statuses"},{value:"pending",label:"Pending"},{value:"under_review",label:"Under review"},{value:"additional_information_required",label:"More information needed"},{value:"approved",label:"Approved"},{value:"rejected",label:"Rejected"}]} />
      {kycQueueQuery.isLoading ? <div className="panel"><p className="muted">Loading review queue…</p></div> : visibleQueue.length ? (
        <ModuleDataTable rows={visibleQueue} empty="No matching review cases." columns={[
          {key:"customer",label:"Customer",render:(customer) => <><b>{customer.full_name}</b><small className="kyc-email">{customer.email}</small></>},
          {key:"documents",label:"Documents",render:(customer) => customer.document_count ?? 0},
          {key:"status",label:"Current status",render:(customer) => <StatePill value={customer.kyc_status} />},
          {key:"case",label:"Review case",render:(customer) => <button className="button primary" type="button" onClick={() => void openReview(customer.id)}>View portal & decide</button>},
        ]} />
      ) : <div className="panel"><Empty text={search || statusFilter !== "all" ? "No KYC records match those filters." : "No customer records are available for review."} /></div>}

      {(loadingDetails || selected || detailError) && <div className="review-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeReview(); }}>
        <section className="review-modal" role="dialog" aria-modal="true" aria-labelledby="kyc-review-title">
          <div className="review-modal-heading"><div><span className="eyebrow">CUSTOMER VERIFICATION</span><h2 id="kyc-review-title">{selected?.full_name ?? (loadingDetails ? "Loading review case…" : "Review case")}</h2></div><button className="review-close" type="button" onClick={closeReview} aria-label="Close review">×</button></div>
          {detailError && <div className="notice error">{detailError}</div>}
          {selected && <>
            <div className="review-customer-grid">
              <div><small>Email</small><b>{selected.email}</b></div>
              <div><small>Phone</small><b>{selected.phone || "Not provided"}</b></div>
              <div><small>Location</small><b>{[selected.city, selected.state, selected.country].filter(Boolean).join(", ") || "Not provided"}</b></div>
              <div><small>Nationality</small><b>{selected.nationality || "Not provided"}</b></div>
              <div><small>Current KYC status</small><StatePill value={selected.kyc_status} /></div>
            </div>
            <div className="review-documents"><h3>Identity documents</h3>
              {selected.documents.length ? selected.documents.map((doc) => <div className="review-document-row" key={doc.id}><span><b>{doc.document_type}</b><small>{new Date(doc.created_at).toLocaleDateString()} · {doc.status.replaceAll("_", " ")}</small></span><button type="button" className="auth-secondary-button" onClick={() => void viewDocument(doc.id, doc.document_type)}>View document</button></div>) : <p className="muted">No documents uploaded yet.</p>}
            </div>
            {preview && <div className="document-preview"><div><b>{preview.name}</b><button type="button" className="text-link" onClick={() => { URL.revokeObjectURL(preview.url); setPreview(null); }}>Close preview</button></div>{preview.type.startsWith("image/") ? <Image src={preview.url} width={1000} height={700} unoptimized alt={`${preview.name} document preview`} /> : <iframe src={preview.url} title={`${preview.name} document preview`} />}</div>}
            <form className="stack-form review-decision-form" onSubmit={submitDecision}>
              <label>Decision<select value={decision} onChange={(event) => setDecision(event.target.value as (typeof decisions)[number])}>{decisions.map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
              <label>Decision note{decision !== "approved" && " · required"}<textarea name="reason" rows={3} maxLength={500} required={decision !== "approved"} placeholder="Record what was checked or what the customer needs to provide." /></label>
              <button className="button primary" type="submit">Record decision</button>
            </form>
          </>}
        </section>
      </div>}
    </>
  );
}
