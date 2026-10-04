"use client";

import {
  Notice,
  PageTitle,
  StatePill,
  Transactions,
} from "../screen-primitives";
import { BeneficiaryForm, TransferForm } from "../screen-actions";
import { api } from "@/lib/api";
import type { CustomerScreenProps } from "./types";

export function TransferScreen(props: CustomerScreenProps) {
  const {
    pathname,
    accountData,
    beneficiaryData,
    transactionData,
    error,
    success,
    run,
  } = props;
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
            Recipient verification is simulated in this demo; no bank lookup is
            performed.
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
}
