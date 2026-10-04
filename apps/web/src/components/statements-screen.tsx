"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api, downloadStatement, money } from "@/lib/api";
import { Notice, PageTitle, Transactions } from "./screen-primitives";
import type { Account } from "./screen-types";

export function StatementScreen({ accounts }: { accounts: Account[] }) {
  const [selected, setSelected] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const { data, error, isLoading } = useQuery({
    queryKey: ["statement", selected],
    queryFn: () =>
      api<{
        account_id: number;
        currency: string;
        closing_balance: string;
        transactions: {
          reference: string;
          type: string;
          amount: string;
          status: string;
          date: string;
        }[];
      }>(`/accounts/${selected}/statement`),
    enabled: Boolean(selected),
  });
  async function exportCsv() {
    try {
      setDownloadError("");
      await downloadStatement(Number(selected));
    } catch (cause) {
      setDownloadError(
        cause instanceof Error ? cause.message : "Could not download statement",
      );
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ACCOUNT ACTIVITY"
        title="Statements"
        copy="Review posted activity and your current closing balance."
      />
      <div className="panel statement-panel">
        <label>
          Choose account
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">Select an account</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.account_type} · {a.account_number_masked}
              </option>
            ))}
          </select>
        </label>
        {data && (
          <>
            <div className="statement-balance">
              <span>Current balance</span>
              <b>{money(data.closing_balance, data.currency)}</b>
              <button className="button primary" onClick={exportCsv}>
                Download CSV
              </button>
            </div>
            <Transactions
              rows={data.transactions.map((tx, id) => ({
                ...tx,
                id,
                currency: data.currency,
                created_at: tx.date,
              }))}
            />
          </>
        )}
        {isLoading && <p className="muted">Loading statement…</p>}
        {error && <Notice error={error.message} />}
        {downloadError && <Notice error={downloadError} />}
      </div>
    </>
  );
}
