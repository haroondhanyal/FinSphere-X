"use client";

import { useQuery } from "@tanstack/react-query";
import { api, downloadStatement, money } from "@/lib/api";
import {
  Notice,
  PageTitle,
  StatePill,
  Transactions,
} from "./screen-primitives";
import type { Account } from "./screen-types";

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
