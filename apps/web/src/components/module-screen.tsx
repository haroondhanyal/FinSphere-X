"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { api, money, sumMoneyAmounts } from "@/lib/api";
import {
  type Account,
  type Beneficiary,
  type Card,
  type Profile,
  type Transaction,
} from "./screen-types";
import {
  Empty,
  Metric,
  Notice,
  PageTitle,
  StatePill,
  Transactions,
} from "./screen-primitives";
import {
  BeneficiaryForm,
  CreateAccount,
  DocumentUpload,
  IssueCard,
  KycForm,
  LimitEditor,
  TransferForm,
  WalletMove,
} from "./screen-actions";
import { AccountDetailScreen, StatementScreen } from "./screen-statements";

export function ModuleScreen() {
  const pathname = usePathname().replace(/\/$/, "") || "/dashboard";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const accountQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api<Account[]>("/accounts"),
    enabled:
      pathname === "/accounts" ||
      pathname === "/dashboard" ||
      pathname === "/transfers" ||
      pathname === "/payments" ||
      pathname === "/cards" ||
      pathname === "/statements",
  });
  const beneficiariesQuery = useQuery({
    queryKey: ["beneficiaries"],
    queryFn: () => api<Beneficiary[]>("/beneficiaries"),
    enabled: pathname === "/transfers" || pathname === "/payments",
  });
  const transactionsQuery = useQuery({
    queryKey: ["transactions"],
    queryFn: () => api<Transaction[]>("/transactions"),
    enabled:
      pathname === "/dashboard" ||
      pathname === "/transfers" ||
      pathname === "/payments",
  });
  const cardsQuery = useQuery({
    queryKey: ["cards"],
    queryFn: () => api<Card[]>("/cards"),
    enabled: pathname === "/cards" || pathname === "/dashboard",
  });
  const walletQuery = useQuery({
    queryKey: ["wallet"],
    queryFn: () =>
      api<{ currency: string; balance: string; level: string; status: string }>(
        "/wallet",
      ),
    enabled: pathname === "/wallet" || pathname === "/dashboard",
  });
  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: () => api<Profile>("/customers/me"),
    enabled: pathname === "/profile",
  });
  const accountData = accountQuery.data ?? [];
  const beneficiaryData = beneficiariesQuery.data ?? [];
  const transactionData = transactionsQuery.data ?? [];
  const cardData = cardsQuery.data ?? [];
  const walletData = walletQuery.data;
  const profileData = profileQuery.data;
  const balance = sumMoneyAmounts(
    accountData.map((account) => account.balance),
  );

  const refresh = () => queryClient.invalidateQueries();
  const run = async (action: () => Promise<unknown>, message: string) => {
    setError("");
    setSuccess("");
    try {
      await action();
      setSuccess(message);
      refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Action failed");
    }
  };

  if (pathname === "/dashboard")
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
                View all →
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

  if (pathname.startsWith("/accounts/") && pathname !== "/accounts/")
    return <AccountDetailScreen accountId={Number(pathname.split("/")[2])} />;

  if (pathname === "/accounts")
    return (
      <>
        <PageTitle
          eyebrow="YOUR MONEY"
          title="Accounts"
          copy="Manage your current and savings accounts in one place."
        />
        <Notice error={error} success={success} />
        <div className="account-cards">
          {accountData.map((a) => (
            <article className="account-card" key={a.id}>
              <div className="account-card-top">
                <span className="account-symbol">{a.currency.slice(0, 1)}</span>
                <StatePill value={a.status} />
              </div>
              <span className="eyebrow">
                {a.account_type.toUpperCase()} ACCOUNT
              </span>
              <strong>{money(a.balance, a.currency)}</strong>
              <span className="muted">
                {a.account_number_masked} · {a.currency}
              </span>
              <Link className="text-link" href={`/accounts/${a.id}`}>
                View account →
              </Link>
            </article>
          ))}
        </div>
        <CreateAccount
          onDone={() =>
            run(
              () =>
                api("/accounts", {
                  method: "POST",
                  body: JSON.stringify({
                    account_type: "savings",
                    currency: "PKR",
                  }),
                }),
              "Savings account opened.",
            )
          }
        />
      </>
    );

  if (pathname === "/wallet")
    return (
      <>
        <PageTitle
          eyebrow="DIGITAL WALLET"
          title="Your wallet"
          copy="A simple way to keep everyday spending money close."
        />
        <Notice error={error} success={success} />
        <div className="wallet-hero">
          <span className="metric-label">AVAILABLE WALLET BALANCE</span>
          <strong>
            {money(walletData?.balance ?? 0, walletData?.currency)}
          </strong>
          <div className="wallet-details">
            <span>
              Wallet tier <b>{walletData?.level ?? "Basic"}</b>
            </span>
            <span>
              Daily transfer limit <b>{money(50000)}</b>
            </span>
            <StatePill value={walletData?.status ?? "active"} />
          </div>
          <WalletMove
            accounts={accountData}
            onMove={(body) =>
              run(
                () =>
                  api("/wallet/transfers", {
                    method: "POST",
                    headers: { "Idempotency-Key": crypto.randomUUID() },
                    body: JSON.stringify(body),
                  }),
                "Wallet balance updated.",
              )
            }
          />
          <div className="info-banner">
            Wallet moves post immediately between your own linked account and
            wallet. Check the amount before confirming.
          </div>
        </div>
      </>
    );

  if (pathname === "/transfers" || pathname === "/payments")
    return (
      <>
        <PageTitle
          eyebrow={pathname === "/payments" ? "PAYMENTS" : "MOVE MONEY"}
          title={pathname === "/payments" ? "Payments" : "Transfers"}
          copy="Send money to a saved recipient with a clear amount and confirmation."
        />
        <Notice error={error} success={success} />
        <div className="two-column">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">
                  NEW {pathname === "/payments" ? "PAYMENT" : "TRANSFER"}
                </span>
                <h3>Recipient and amount</h3>
              </div>
              <span className="step-badge">01 / 01</span>
            </div>
            <TransferForm
              accounts={accountData}
              beneficiaries={beneficiaryData}
              isPayment={pathname === "/payments"}
              onSubmit={(input) =>
                run(
                  () =>
                    api(pathname === "/payments" ? "/payments" : "/transfers", {
                      method: "POST",
                      headers: { "Idempotency-Key": crypto.randomUUID() },
                      body: JSON.stringify(input),
                    }),
                  "Your transaction has been posted.",
                )
              }
            />
          </div>
          <div className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">SAVED RECIPIENTS</span>
                <h3>Beneficiaries</h3>
              </div>
            </div>
            <p className="form-hint">
              Recipient verification is simulated in this demo; no bank lookup
              is performed.
            </p>
            <BeneficiaryForm
              onAdd={(input) =>
                run(
                  () =>
                    api("/beneficiaries", {
                      method: "POST",
                      body: JSON.stringify(input),
                    }),
                  "Recipient added.",
                )
              }
            />
            {beneficiaryData.map((b) => (
              <div className="beneficiary-row" key={b.id}>
                <span className="avatar">{b.name.slice(0, 1)}</span>
                <span>
                  <b>{b.name}</b>
                  <small>
                    {b.account_number_masked} · {b.bank_name}
                  </small>
                </span>
                {b.is_verified ? (
                  <StatePill value="verified" />
                ) : (
                  <button
                    className="small-button"
                    onClick={() =>
                      run(
                        () =>
                          api(`/beneficiaries/${b.id}/verify`, {
                            method: "POST",
                          }),
                        "Recipient verified.",
                      )
                    }
                  >
                    Mark verified (demo)
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="panel table-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">HISTORY</span>
              <h3>Recent transactions</h3>
            </div>
          </div>
          <Transactions rows={transactionData} />
        </div>
      </>
    );

  if (pathname === "/cards")
    return (
      <>
        <PageTitle
          eyebrow="CARD MANAGEMENT"
          title="Cards"
          copy="Issue a virtual or debit card and manage its status and daily limit."
        />
        <Notice error={error} success={success} />
        <div className="cards-grid">
          {cardData.map((card) => (
            <article className="bank-card" key={card.id}>
              <div className="card-brand">
                FinSphere<span>X</span>
              </div>
              <span className="card-chip" />
              <strong>•••• &nbsp;•••• &nbsp;•••• &nbsp;{card.last4}</strong>
              <div className="card-bottom">
                <span>
                  FINSPHERE CUSTOMER
                  <small>{card.card_type.toUpperCase()}</small>
                </span>
                <StatePill value={card.status} />
              </div>
            </article>
          ))}
        </div>
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">CARD CONTROLS</span>
              <h3>Manage your cards</h3>
            </div>
            <IssueCard
              accounts={accountData}
              onIssue={(account_id) =>
                run(
                  () =>
                    api("/cards", {
                      method: "POST",
                      body: JSON.stringify({
                        account_id,
                        card_type: "virtual",
                      }),
                    }),
                  "Virtual card issued and ready to activate.",
                )
              }
            />
          </div>
          {cardData.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Card</th>
                    <th>Type</th>
                    <th>Daily limit</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {cardData.map((c) => (
                    <tr key={c.id}>
                      <td>{c.masked_number}</td>
                      <td>{c.card_type}</td>
                      <td>
                        <LimitEditor
                          value={c.daily_limit}
                          onSave={(daily_limit) =>
                            run(
                              () =>
                                api(`/cards/${c.id}/limit`, {
                                  method: "PATCH",
                                  body: JSON.stringify({ daily_limit }),
                                }),
                              "Daily card limit updated.",
                            )
                          }
                        />
                      </td>
                      <td>
                        <StatePill value={c.status} />
                      </td>
                      <td>
                        <div className="inline-actions">
                          {c.status === "inactive" && (
                            <button
                              onClick={() =>
                                run(
                                  () =>
                                    api(`/cards/${c.id}/activate`, {
                                      method: "POST",
                                    }),
                                  "Card activated.",
                                )
                              }
                            >
                              Activate
                            </button>
                          )}
                          {c.status === "active" && (
                            <button
                              onClick={() =>
                                run(
                                  () =>
                                    api(`/cards/${c.id}/freeze`, {
                                      method: "POST",
                                    }),
                                  "Card frozen.",
                                )
                              }
                            >
                              Freeze
                            </button>
                          )}
                          {c.status === "frozen" && (
                            <button
                              onClick={() =>
                                run(
                                  () =>
                                    api(`/cards/${c.id}/unfreeze`, {
                                      method: "POST",
                                    }),
                                  "Card unfrozen.",
                                )
                              }
                            >
                              Unfreeze
                            </button>
                          )}
                          {c.status !== "blocked" && (
                            <button
                              className="danger-link"
                              onClick={() =>
                                run(
                                  () =>
                                    api(`/cards/${c.id}/block`, {
                                      method: "POST",
                                    }),
                                  "Card blocked.",
                                )
                              }
                            >
                              Block
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty text="You have no cards yet. Issue a virtual card to get started." />
          )}
        </div>
      </>
    );

  if (pathname === "/statements")
    return <StatementScreen accounts={accountData} />;

  if (pathname === "/profile" || pathname === "/security")
    return (
      <>
        <PageTitle
          eyebrow="PERSONAL DETAILS"
          title={pathname === "/security" ? "Security" : "Profile & KYC"}
          copy={
            pathname === "/security"
              ? "Manage your signed-in session and review your account security."
              : "Keep your customer information and verification status up to date."
          }
        />
        <Notice error={error} success={success} />
        {pathname === "/profile" && profileData ? (
          <div className="two-column">
            <div className="panel detail-list">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">CUSTOMER PROFILE</span>
                  <h3>{profileData.full_name}</h3>
                </div>
                <StatePill value={profileData.kyc_status} />
              </div>
              <p>
                <span>Email</span>
                <b>{profileData.email}</b>
              </p>
              <p>
                <span>Phone</span>
                <b>{profileData.phone || "Not provided"}</b>
              </p>
              <p>
                <span>Nationality</span>
                <b>{profileData.nationality || "Not provided"}</b>
              </p>
              <KycForm
                onUpdate={(nationality) =>
                  run(
                    () =>
                      api("/customers/me/kyc", {
                        method: "PATCH",
                        body: JSON.stringify({ nationality }),
                      }),
                    "KYC details submitted for review.",
                  )
                }
              />
            </div>
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">IDENTITY DOCUMENTS</span>
                  <h3>Upload for verification</h3>
                </div>
              </div>
              <DocumentUpload
                onUpload={(form) =>
                  run(
                    () =>
                      api(
                        `/customers/me/kyc/documents?document_type=${encodeURIComponent(String(form.get("document_type")))}`,
                        { method: "POST", body: form },
                      ),
                    "Document uploaded for review.",
                  )
                }
              />
            </div>
          </div>
        ) : pathname === "/security" ? (
          <div className="panel detail-list">
            <span className="eyebrow">SIGNED IN</span>
            <h3>Session controls</h3>
            <p>
              <span>Access token</span>
              <b>Stored in this browser session</b>
            </p>
            <p>
              <span>Authentication</span>
              <b>Email and password</b>
            </p>
            <p>
              <span>Multi-factor authentication</span>
              <b>Planned for a later phase</b>
            </p>
            <div className="info-banner">
              Use a unique password. Your session expires after 30 minutes.
            </div>
          </div>
        ) : (
          <Empty text="Loading customer profile…" />
        )}
      </>
    );

  return (
    <>
      <PageTitle
        eyebrow="FINSPHERE X"
        title="Page coming soon"
        copy="This screen is planned for a later product phase."
      />
      <div className="panel">
        <p className="muted">
          Use the navigation to explore account, wallet, transfer, payment,
          card, statement and profile screens available in this release.
        </p>
      </div>
    </>
  );
}
