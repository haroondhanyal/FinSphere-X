"use client";

import Link from "next/link";
import { api, money } from "@/lib/api";
import { Notice, PageTitle, StatePill } from "../screen-primitives";
import { CreateAccount } from "../screen-actions";
import type { CustomerScreenProps } from "./types";

export function AccountsScreen(props: CustomerScreenProps) {
  const { accountData, error, success, run } = props;
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
        onDone={(input) =>
          run(
            () =>
              api("/accounts", {
                method: "POST",
                body: JSON.stringify(input),
              }),
            "Your new account is ready.",
          )
        }
      />
    </>
  );
}
