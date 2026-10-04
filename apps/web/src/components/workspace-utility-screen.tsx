"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { Empty, PageTitle, StatePill } from "./screen-primitives";

type Ticket = { id: number; subject: string; category: string; body: string; status: string; staff_response: string; created_at: string };
type Budget = { id: number; month: string; category: string; limit_amount: string; spent: string; remaining: string; currency: string };
type Goal = { id: number; name: string; target_amount: string; current_amount: string; currency: string; target_date: string | null; progress_percent: number; status: string; disclosure: string };

export function WorkspaceUtilityScreen({ section }: { section: string }) {
  const cache = useQueryClient();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const roleQuery = useQuery<{ role: string }>({ queryKey: ["utility-role"], queryFn: () => api("/auth/me") });
  const query = useQuery<unknown>({
    queryKey: ["workspace-utility", section],
    queryFn: async () => {
      if (section === "support") return api<Ticket[]>("/support/tickets");
      if (section === "notifications") return api<{ items: { id: number; title: string; detail: string; created_at: string; resource: string }[]; source: string }>("/notifications");
      if (section === "budgets") return api<Budget[]>("/budgets");
      if (section === "goals") return api<Goal[]>("/goals");
      if (section === "deposits") {
        const [products, positions, accounts] = await Promise.all([
          api<Record<string, unknown>[]>("/deposits/products"),
          api<Record<string, unknown>[]>("/deposits/positions"),
          api<{ id: number; account_number_masked: string; balance: string; currency: string }[]>("/accounts"),
        ]);
        return { products, positions, accounts };
      }
      if (section === "onboarding") return api<{ full_name: string; email: string; phone: string; country: string; city: string; kyc_status: string }>("/customers/me");
      return null;
    },
  });
  async function act(request: () => Promise<unknown>, message: string) {
    setError("");
    setNotice("");
    try {
      await request();
      setNotice(message);
      await cache.invalidateQueries({ queryKey: ["workspace-utility", section] });
      await cache.invalidateQueries({ queryKey: ["notifications"] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Request failed");
    }
  }
  const handle = (submit: (data: FormData) => Promise<unknown>, message: string) => (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    void act(() => submit(data), message).then(() => form.reset());
  };
  const banners = <>{notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}</>;

  if (section === "onboarding") {
    const profile = query.data as { full_name: string; email: string; phone: string; country: string; city: string; kyc_status: string } | undefined;
    return <>
      <PageTitle eyebrow="ACCOUNT SETUP" title="Onboarding checklist" copy="Finish your profile and submit identity documents for human review." />
      {query.isLoading ? <div className="panel">Loading onboarding status…</div> : profile ? <div className="panel onboarding-checklist">
        <div className="onboarding-step"><StatePill value="complete" /><div><b>Account created</b><small>{profile.email}</small></div></div>
        <div className="onboarding-step"><StatePill value={profile.phone ? "complete" : "incomplete"} /><div><b>Contact details</b><small>{profile.phone || "Add a phone number"}</small></div></div>
        <div className="onboarding-step"><StatePill value={profile.country && profile.city ? "complete" : "incomplete"} /><div><b>Address</b><small>{[profile.city, profile.country].filter(Boolean).join(", ") || "Add your city and country"}</small></div></div>
        <div className="onboarding-step"><StatePill value={profile.kyc_status} /><div><b>Identity verification</b><small>Upload a document and wait for an operations review.</small></div></div>
        <Link className="button primary" href="/profile">Complete profile and KYC</Link>
      </div> : null}
    </>;
  }
  if (section === "support") {
    const rows = (query.data ?? []) as Ticket[];
    const staff = ["operations", "admin"].includes(roleQuery.data?.role ?? "");
    return <>
      <PageTitle eyebrow="HELP CENTER" title="Support cases" copy="Submit a request and follow its review status. Do not include passwords or full card details." />{banners}
      <form className="panel form-stack utility-form" onSubmit={handle((d) => api("/support/tickets", { method: "POST", body: JSON.stringify({ subject: d.get("subject"), category: d.get("category"), body: d.get("body") }) }), "Support request submitted.")}>
        <h3>Open a support request</h3><label>Subject<input name="subject" minLength={4} maxLength={160} required /></label>
        <label>Category<select name="category"><option value="accounts">Accounts</option><option value="cards">Cards</option><option value="payments">Payments</option><option value="profile">Profile</option><option value="other">Other</option></select></label>
        <label>What do you need help with?<textarea name="body" minLength={10} maxLength={4000} required /></label><button>Submit request</button>
      </form>
      <section className="panel"><h3>{staff ? "Support queue" : "Your requests"}</h3>{query.error && <p className="notice error">{query.error.message}</p>}
        {rows.length ? <div className="utility-list">{rows.map((row) => <article className="utility-card" key={row.id}>
          <div className="utility-card-title"><div><small>#{row.id} · {row.category}</small><h4>{row.subject}</h4></div><StatePill value={row.status} /></div>
          <p>{row.body}</p>{row.staff_response && <div className="info-banner"><b>Support reply:</b> {row.staff_response}</div>}
          {staff && row.status !== "closed" && row.status !== "resolved" && <form className="stack-form" onSubmit={handle((d) => api("/support/tickets/" + row.id, { method: "PATCH", body: JSON.stringify({ status: d.get("status"), staff_response: d.get("staff_response") }) }), "Support case updated.")}>
            <label>Response<textarea name="staff_response" minLength={3} maxLength={2000} required /></label><label>Status<select name="status"><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></label><button>Save response</button>
          </form>}
        </article>)}</div> : !query.isLoading && <Empty text="No support requests yet." />}
      </section>
    </>;
  }
  if (section === "notifications") {
    const data = query.data as { items: { id: number; title: string; detail: string; created_at: string; resource: string }[]; source: string } | undefined;
    return <><PageTitle eyebrow="ACTIVITY" title="Notifications" copy="Recent account events and review updates." />{banners}<div className="panel"><p className="form-hint">{data?.source ?? "Recent account activity"} · read status is not tracked.</p>{data?.items.length ? <div className="utility-list">{data.items.map((item) => <article className="utility-card" key={item.id}><div className="utility-card-title"><h4>{item.title}</h4><small>{new Date(item.created_at).toLocaleString()}</small></div><p>{item.detail || item.resource}</p></article>)}</div> : !query.isLoading && <Empty text="No recent activity to show." />}</div></>;
  }
  if (section === "budgets") {
    const rows = (query.data ?? []) as Budget[];
    const currentMonth = new Date().toISOString().slice(0, 7);
    return <><PageTitle eyebrow="MONEY PLANNING" title="Monthly budgets" copy="Set category limits and compare them with posted account activity." />{banners}
      <form className="panel form-stack utility-form" onSubmit={handle((d) => api("/budgets", { method: "POST", body: JSON.stringify({ month: d.get("month"), category: d.get("category"), limit_amount: d.get("limit_amount"), currency: "PKR" }) }), "Budget saved.")}>
        <h3>Create or update a budget</h3><label>Month<input type="month" name="month" defaultValue={currentMonth} required /></label><label>Category<select name="category"><option value="transfers">Transfers</option><option value="payments">Payments</option><option value="wallet">Wallet withdrawals</option></select></label><label>Monthly limit (PKR)<input type="number" name="limit_amount" min="1" step="0.01" required /></label><button>Save budget</button>
      </form><div className="utility-grid">{rows.map((row) => <article className="panel utility-card" key={row.id}><div className="utility-card-title"><h3>{row.category} · {row.month}</h3><b>{row.currency}</b></div><p>Limit <strong>{row.limit_amount}</strong></p><p>Posted spend <strong>{row.spent}</strong></p><p>Remaining <strong>{row.remaining}</strong></p></article>)}{!query.isLoading && !rows.length && <Empty text="No budgets set yet." />}</div>
    </>;
  }
  if (section === "goals") {
    const rows = (query.data ?? []) as Goal[];
    return <><PageTitle eyebrow="MONEY PLANNING" title="Savings goals" copy="Track personal targets. Contributions here are tracking entries and do not move funds." />{banners}
      <form className="panel form-stack utility-form" onSubmit={handle((d) => api("/goals", { method: "POST", body: JSON.stringify({ name: d.get("name"), target_amount: d.get("target_amount"), currency: "PKR", target_date: d.get("target_date") || null }) }), "Savings goal created.")}>
        <h3>Create a goal</h3><label>Goal name<input name="name" minLength={2} maxLength={120} required /></label><label>Target amount (PKR)<input name="target_amount" type="number" min="1" step="0.01" required /></label><label>Target date<input name="target_date" type="date" /></label><button>Create goal</button>
      </form><div className="utility-grid">{rows.map((row) => <article className="panel utility-card" key={row.id}><div className="utility-card-title"><h3>{row.name}</h3><StatePill value={row.status} /></div><p>{row.current_amount} / {row.target_amount} {row.currency}</p><progress value={row.progress_percent} max="100" aria-label={row.progress_percent + "% complete"} /><small>{row.disclosure}</small>{row.status === "active" && <form className="stack-form" onSubmit={handle((d) => api("/goals/" + row.id + "/contributions", { method: "POST", body: JSON.stringify({ amount: d.get("amount") }) }), "Goal progress recorded; no funds moved.")}><label>Record progress<input name="amount" type="number" min="0.01" step="0.01" required /></label><button>Update tracker</button></form>}</article>)}{!query.isLoading && !rows.length && <Empty text="No savings goals yet." />}</div>
    </>;
  }
  if (section === "deposits") {
    const data = query.data as { products: Record<string, unknown>[]; positions: Record<string, unknown>[]; accounts: { id: number; account_number_masked: string; balance: string; currency: string }[] } | undefined;
    return <><PageTitle eyebrow="SAVINGS PRODUCTS" title="Term deposits" copy="Review illustrative terms and track a simulated position." />{banners}
      <div className="utility-grid">{data?.products.map((product) => <article className="panel utility-card" key={String(product.code)}><h3>{String(product.name)}</h3><p>{String(product.annual_yield)}% illustrative yield · minimum {String(product.minimum)} {String(product.currency)}</p><small>{String(product.disclosure)}</small></article>)}</div>
      <form className="panel form-stack utility-form" onSubmit={handle((d) => api("/deposits/positions", { method: "POST", body: JSON.stringify({ source_account_id: Number(d.get("account_id")), product_code: d.get("product_code"), amount: d.get("amount") }) }), "Simulated position recorded; no money moved.")}>
        <h3>Preview a position</h3><label>Account<select name="account_id" required>{data?.accounts.map((account) => <option value={account.id} key={account.id}>{account.account_number_masked} · {account.balance} {account.currency}</option>)}</select></label><label>Product<select name="product_code" required>{data?.products.map((product) => <option value={String(product.code)} key={String(product.code)}>{String(product.name)}</option>)}</select></label><label>Amount<input name="amount" type="number" min="1" step="0.01" required /></label><button disabled={!data?.products.length || !data?.accounts.length}>Record simulation</button>
      </form><div className="utility-grid">{data?.positions.map((position, index) => <article className="panel utility-card" key={String(position.id ?? index)}><h3>Simulated position</h3><pre>{JSON.stringify(position, null, 2)}</pre></article>)}</div>
    </>;
  }
  return <PageTitle eyebrow="WORKSPACE" title="Not found" copy="This workspace section is not available." />;
}
