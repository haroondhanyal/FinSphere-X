"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, downloadStatement, money } from "@/lib/api";
import {
  Notice,
  PageTitle,
  StatePill,
  Transactions,
} from "./screen-primitives";
import { type Account } from "./screen-types";

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

export function AccountDetailScreen({ accountId }: { accountId: number }) {
  const { data, error, isLoading } = useQuery({
    queryKey: ["account-detail", accountId],
    queryFn: async () => {
      const [account, statement] = await Promise.all([
        api<Account>(`/accounts/${accountId}`),
        api<{
          closing_balance: string;
          currency: string;
          transactions: {
            reference: string;
            type: string;
            amount: string;
            status: string;
            date: string;
          }[];
        }>(`/accounts/${accountId}/statement`),
      ]);
      return { account, statement };
    },
  });
  if (error)
    return (
      <>
        <PageTitle
          eyebrow="ACCOUNT"
          title="Account unavailable"
          copy="This account could not be loaded."
        />
        <Notice error={error.message} />
      </>
    );
  if (isLoading || !data)
    return <div className="loading">Loading account…</div>;
  return (
    <>
      <PageTitle
        eyebrow="ACCOUNT DETAILS"
        title={`${data.account.account_type} account`}
        copy={`${data.account.account_number_masked} · ${data.account.currency}`}
      />
      <div className="panel">
        <div className="statement-balance">
          <span>Available and ledger balance</span>
          <b>{money(data.account.balance, data.account.currency)}</b>
          <StatePill value={data.account.status} />
        </div>
        <div className="panel-heading">
          <h3>Account activity</h3>
          <button
            className="button primary"
            onClick={() => downloadStatement(accountId)}
          >
            Download CSV
          </button>
        </div>
        <Transactions
          rows={data.statement.transactions.map((tx, id) => ({
            ...tx,
            id,
            currency: data.account.currency,
            created_at: tx.date,
          }))}
        />
      </div>
    </>
  );
}
