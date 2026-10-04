"use client";

import Link from "next/link";
import { money } from "@/lib/api";
import {
  Empty,
  Metric,
  Notice,
  PageTitle,
  StatePill,
} from "../screen-primitives";
import type { CustomerScreenProps } from "./types";

export function DashboardScreen(props: CustomerScreenProps) {
  const {
    accountData,
    transactionData,
    cardData,
    walletData,
    balance,
    accountQuery,
    walletQuery,
    cardsQuery,
    transactionsQuery,
  } = props;
  return (
    <>
      <div className="welcome-row">
        <div>
          <PageTitle
            eyebrow="YOUR FINANCIAL HOME"
            title="Good to see you"
            copy="A clear view of your accounts and everyday money."
          />
        </div>
        <span className="date-label">Personal banking · PKR</span>
      </div>
      <section className="metric-grid">
        <article className="balance-card">
          <span className="metric-label">TOTAL ACCOUNT BALANCE</span>
          <strong>{money(balance)}</strong>
          <span className="balance-foot">
            Current balance across {accountData.length} accounts
          </span>
          <div className="balance-orbit orbit-one" />
          <div className="balance-orbit orbit-two" />
        </article>
        <Metric
          label="WALLET BALANCE"
          value={money(walletData?.balance ?? 0)}
          sub={`${walletData?.level ?? "Basic"} wallet`}
          tone="mint"
        />
        <Metric
          label="ACTIVE CARDS"
          value={String(
            cardData.filter((card) => card.status === "active").length,
          )}
          sub={`${cardData.length} cards issued`}
          tone="violet"
        />
        <Metric
          label="RECENT ACTIVITY"
          value={String(transactionData.length)}
          sub="Posted transactions"
          tone="amber"
        />
      </section>
      <section className="panel-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">YOUR ACCOUNTS</span>
              <h3>Accounts at a glance</h3>
            </div>
            <Link href="/accounts" className="text-link">
              View / open account →
            </Link>
          </div>
          {accountData.length ? (
            <div className="account-list">
              {accountData.map((a) => (
                <div className="account-row" key={a.id}>
                  <span className="account-symbol">
                    {a.currency.slice(0, 1)}
                  </span>
                  <span className="account-info">
                    <b>{a.account_type} account</b>
                    <small>
                      {a.account_number_masked} · {a.currency}
                    </small>
                  </span>
                  <span className="account-value">
                    {money(a.balance, a.currency)}
                  </span>
                  <StatePill value={a.status} />
                </div>
              ))}
            </div>
          ) : (
            <Empty text="Your accounts will appear here." />
          )}
        </div>
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">LATEST</span>
              <h3>Recent activity</h3>
            </div>
            <Link href="/transfers" className="text-link">
              Activity →
            </Link>
          </div>
          {transactionData.length ? (
            <div className="activity-list">
              {transactionData.slice(0, 5).map((tx) => (
                <div className="activity-row" key={tx.id}>
                  <span className="activity-icon">↗</span>
                  <span>
                    <b>{tx.type}</b>
                    <small>{tx.reference}</small>
                  </span>
                  <span className="activity-amount">
                    − {money(tx.amount, tx.currency)}
                    <small>
                      <StatePill value={tx.status} />
                    </small>
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <Empty text="No transactions yet. Your activity will show here." />
          )}
        </div>
      </section>
      <Notice
        error={
          accountQuery.error?.message ??
          walletQuery.error?.message ??
          cardsQuery.error?.message ??
          transactionsQuery.error?.message
        }
      />
    </>
  );
}
