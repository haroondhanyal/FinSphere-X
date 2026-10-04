"use client";

import { api, money } from "@/lib/api";
import { Notice, PageTitle, StatePill } from "../screen-primitives";
import { WalletMove } from "../screen-actions";
import type { CustomerScreenProps } from "./types";

export function WalletScreen(props: CustomerScreenProps) {
  const { walletData, accountData, error, success, run } = props;
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
        <strong>{money(walletData?.balance ?? 0, walletData?.currency)}</strong>
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
}
