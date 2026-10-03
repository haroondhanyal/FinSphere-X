"use client";

import { money } from "@/lib/api";
import { type Transaction } from "./screen-types";

export function Notice({
  error,
  success,
}: {
  error?: string;
  success?: string;
}) {
  return error ? (
    <div className="notice error">{error}</div>
  ) : success ? (
    <div className="notice success">{success}</div>
  ) : null;
}

export function StatePill({ value }: { value: string }) {
  return (
    <span className={`pill ${value.toLowerCase().replaceAll("_", "-")}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function PageTitle({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string;
  title: string;
  copy: string;
}) {
  return (
    <div className="page-title">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{copy}</p>
      </div>
    </div>
  );
}

export function Metric({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  tone: string;
}) {
  return (
    <article className={`metric-card ${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </article>
  );
}

export function Empty({ text }: { text: string }) {
  return (
    <div className="empty-state">
      <span>◇</span>
      <p>{text}</p>
    </div>
  );
}

export function Transactions({ rows }: { rows: Transaction[] }) {
  return rows.length ? (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Reference</th>
            <th>Type</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((tx) => (
            <tr key={tx.id}>
              <td className="mono">{tx.reference}</td>
              <td>{tx.type}</td>
              <td>{money(tx.amount, tx.currency)}</td>
              <td>
                <StatePill value={tx.status} />
              </td>
              <td>{new Date(tx.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty text="No transactions to display yet." />
  );
}
