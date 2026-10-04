"use client";

import { type FormEvent, useState } from "react";
import { money } from "@/lib/api";
import { type Account, type Beneficiary } from "./screen-types";

export function CreateAccount({ onDone }: { onDone: (input: { account_type: string; currency: string }) => void }) {
  const [accountType, setAccountType] = useState("savings");
  const [currency, setCurrency] = useState("PKR");
  return (
    <form className="panel action-panel account-create-form" onSubmit={(event) => { event.preventDefault(); onDone({ account_type: accountType, currency }); }}>
      <div className="account-create-copy">
        <span className="eyebrow">NEED ANOTHER ACCOUNT?</span>
        <h3>Open a new account</h3>
        <p className="muted">Choose the account type and currency for your new account.</p>
      </div>
      <label>Account type<select value={accountType} onChange={(event) => setAccountType(event.target.value)}><option value="current">Current</option><option value="savings">Savings</option><option value="salary">Salary</option></select></label>
      <label>Currency<select value={currency} onChange={(event) => setCurrency(event.target.value)}><option>PKR</option><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option><option>SAR</option></select></label>
      <button className="button primary" type="submit">
        Create account
      </button>
    </form>
  );
}
export function BeneficiaryForm({
  onAdd,
}: {
  onAdd: (input: {
    name: string;
    account_number: string;
    bank_name: string;
    currency: string;
  }) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open ? (
        <form
          className="stack-form"
          onSubmit={(e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget);
            onAdd({
              name: String(form.get("name")),
              account_number: String(form.get("account_number")),
              bank_name: String(form.get("bank_name")),
              currency: "PKR",
            });
            setOpen(false);
          }}
        >
          <input
            name="name"
            aria-label="Recipient name"
            placeholder="Recipient name"
            required
          />
          <input
            name="account_number"
            aria-label="Account number"
            placeholder="Account number"
            required
            minLength={6}
          />
          <input
            name="bank_name"
            aria-label="Bank name"
            placeholder="Bank name"
            defaultValue="FinSphere X"
            required
          />
          <button className="button primary">Save recipient</button>
        </form>
      ) : (
        <button
          className="text-link add-beneficiary"
          onClick={() => setOpen(true)}
        >
          + Add beneficiary
        </button>
      )}
    </>
  );
}
export function TransferForm({
  accounts,
  beneficiaries,
  isPayment,
  onSubmit,
}: {
  accounts: Account[];
  beneficiaries: Beneficiary[];
  isPayment: boolean;
  onSubmit: (input: object) => void;
}) {
  const [account, setAccount] = useState("");
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");
  const selected = accounts.find((a) => a.id === Number(account));
  return (
    <form
      className="stack-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          source_account_id: Number(account),
          beneficiary_id: Number(recipient),
          amount,
          purpose: isPayment ? "Bill payment" : "Transfer",
        });
      }}
    >
      <label>
        From account
        <select
          required
          value={account}
          onChange={(e) => setAccount(e.target.value)}
        >
          <option value="">Choose account</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.account_type} · {a.account_number_masked} ·{" "}
              {money(a.balance, a.currency)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Recipient
        <select
          required
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        >
          <option value="">Choose verified recipient</option>
          {beneficiaries
            .filter((b) => b.is_verified)
            .map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} · {b.account_number_masked}
              </option>
            ))}
        </select>
      </label>
      <label>
        Amount
        <input
          inputMode="decimal"
          pattern="[0-9]+(\.[0-9]{1,4})?"
          required
          min="0.01"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </label>
      <div className="fee-preview">
        <span>Demo transfer fee</span>
        <b>{money(0)}</b>
        <span>You send</span>
        <b>{money(amount || 0, selected?.currency)}</b>
      </div>
      <p className="form-hint">
        Sending posts immediately. Fees are not configured in this demo. Check
        the recipient and amount before sending.
      </p>
      <button
        className="button primary full"
        disabled={!accounts.length || !beneficiaries.some((b) => b.is_verified)}
      >
        Send now
      </button>
    </form>
  );
}
export function IssueCard({
  accounts,
  onIssue,
}: {
  accounts: Account[];
  onIssue: (accountId: number) => void;
}) {
  const [account, setAccount] = useState("");
  return (
    <div className="issue-card">
      <select
        aria-label="Card funding account"
        value={account}
        onChange={(e) => setAccount(e.target.value)}
      >
        <option value="">Choose account</option>
        {accounts.map((a) => (
          <option value={a.id} key={a.id}>
            {a.account_type} · {a.account_number_masked}
          </option>
        ))}
      </select>
      <button
        className="button primary"
        disabled={!account}
        onClick={() => onIssue(Number(account))}
      >
        Issue virtual card
      </button>
    </div>
  );
}
export function WalletMove({
  accounts,
  onMove,
}: {
  accounts: Account[];
  onMove: (body: {
    account_id: number;
    direction: string;
    amount: string;
  }) => void;
}) {
  const [direction, setDirection] = useState("deposit");
  const [account, setAccount] = useState("");
  const [amount, setAmount] = useState("");
  return (
    <form
      className="wallet-move"
      onSubmit={(e) => {
        e.preventDefault();
        onMove({ account_id: Number(account), direction, amount });
      }}
    >
      <label>
        Action
        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
        >
          <option value="deposit">Add money from account</option>
          <option value="withdraw">Withdraw to account</option>
        </select>
      </label>
      <label>
        Linked account
        <select
          required
          value={account}
          onChange={(e) => setAccount(e.target.value)}
        >
          <option value="">Choose account</option>
          {accounts.map((a) => (
            <option value={a.id} key={a.id}>
              {a.account_type} · {a.account_number_masked} ·{" "}
              {money(a.balance, a.currency)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Amount
        <input
          required
          inputMode="decimal"
          pattern="[0-9]+(\.[0-9]{1,4})?"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
        />
      </label>
      <button className="button primary" disabled={!account}>
        {direction === "deposit" ? "Add money" : "Withdraw"}
      </button>
    </form>
  );
}
export function LimitEditor({
  value,
  onSave,
}: {
  value: string;
  onSave: (limit: string) => void;
}) {
  const [limit, setLimit] = useState(value);
  return (
    <form
      className="limit-editor"
      onSubmit={(event) => {
        event.preventDefault();
        onSave(limit);
      }}
    >
      <input
        aria-label="Daily card limit"
        type="number"
        min="1"
        max="10000000"
        step="0.01"
        value={limit}
        onChange={(event) => setLimit(event.target.value)}
      />
      <button type="submit">Save</button>
    </form>
  );
}
export function KycForm({
  onUpdate,
}: {
  onUpdate: (nationality: string) => void;
}) {
  const [nationality, setNationality] = useState("");
  return (
    <form
      className="stack-form inner-form"
      onSubmit={(e) => {
        e.preventDefault();
        onUpdate(nationality);
      }}
    >
      <label>
        Nationality
        <input
          required
          minLength={2}
          maxLength={80}
          value={nationality}
          onChange={(e) => setNationality(e.target.value)}
          placeholder="e.g. Pakistani"
        />
      </label>
      <button className="button primary">Submit KYC details</button>
    </form>
  );
}
export function DocumentUpload({
  onUpload,
}: {
  onUpload: (form: FormData) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState("national_id");
  return (
    <form
      className="stack-form"
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        if (!file) return;
        const form = new FormData();
        form.append("file", file);
        form.append("document_type", type);
        onUpload(form);
      }}
    >
      <label>
        Document type
        <select value={type} onChange={(event) => setType(event.target.value)}>
          <option value="national_id">National ID</option>
          <option value="passport">Passport</option>
          <option value="utility_bill">Utility bill</option>
          <option value="salary_slip">Salary slip</option>
        </select>
      </label>
      <label className="file-drop">
        Select a PDF, PNG or JPEG
        <input
          type="file"
          accept="application/pdf,image/png,image/jpeg"
          required
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {file && (
        <small className="muted">
          {file.name} · {(file.size / 1024).toFixed(0)} KB
        </small>
      )}
      <small className="form-hint">
        Maximum 5 MB. Documents are stored privately and only visible to you.
      </small>
      <button className="button primary" disabled={!file}>
        Upload document
      </button>
    </form>
  );
}
