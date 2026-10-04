"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Notice, PageTitle, StatePill } from "../screen-primitives";
import { ModuleDataTable, ModuleRecordToolbar } from "../module-data-table";
import type { Phase58ScreenProps } from "./types";

type Member = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  kyc_status: string;
  account_count: number;
  created_at: string;
};

const memberRoles = ["customer", "operations", "admin", "business", "merchant"];
const emptyMembers: Member[] = [];

export function MembersScreen(props: Phase58ScreenProps) {
  const { query, working, error, notice, perform, submit } = props;
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [newRole, setNewRole] = useState("customer");
  const rows = (query.data as Member[] | undefined) ?? emptyMembers;
  const filtered = rows.filter((member) =>
    (roleFilter === "all" || member.role === roleFilter) &&
    `${member.full_name} ${member.email}`.toLowerCase().includes(search.trim().toLowerCase()),
  );
  const activeCount = rows.filter((member) => member.is_active).length;

  return <>
    <PageTitle eyebrow="ACCESS MANAGEMENT" title="Members & accounts" copy="Create customer or staff access, provision their account and wallet, and manage access status." />
    <Notice error={error || (query.error instanceof Error ? query.error.message : "")} success={notice} />
    <div className="module-summary-grid">
      <div><span>Total members</span><b>{rows.length}</b></div>
      <div><span>Active access</span><b>{activeCount}</b></div>
      <div><span>Suspended</span><b>{rows.length - activeCount}</b></div>
    </div>
    <form className="panel form-stack member-create-form" onSubmit={submit((data) => api("/admin/members", {
      method: "POST",
      body: JSON.stringify({
        full_name: data.get("full_name"), email: data.get("email"), password: data.get("password"),
        role: data.get("role"), phone: data.get("phone"), country: data.get("country"),
        currency: data.get("currency"), legal_name: data.get("legal_name"),
      }),
    }), "Member created with a customer profile, account and wallet.")}>
      <div><span className="eyebrow">NEW MEMBER</span><h3>Create member account</h3><p className="muted">Customer members start with pending KYC. Business and merchant organizations are created for review.</p></div>
      <div className="member-form-grid">
        <label>Full name<input name="full_name" minLength={2} maxLength={160} required /></label>
        <label>Email<input name="email" type="email" autoComplete="off" required /></label>
        <label>Initial password<input name="password" type="password" minLength={12} maxLength={128} autoComplete="new-password" required /><small>At least 12 characters</small></label>
        <label>Role<select name="role" value={newRole} onChange={(event) => setNewRole(event.target.value)}>{memberRoles.map((role) => <option key={role} value={role}>{role[0].toUpperCase()+role.slice(1)}</option>)}</select></label>
        <label>Phone<input name="phone" maxLength={40} /></label>
        <label>Country<input name="country" maxLength={100} /></label>
        <label>First account currency<select name="currency" defaultValue="PKR">{["PKR","USD","EUR","GBP","AED","SAR"].map((currency) => <option key={currency}>{currency}</option>)}</select></label>
        <label>Organization name <small>{newRole === "business" || newRole === "merchant" ? "required" : "optional"}</small><input name="legal_name" maxLength={180} required={newRole === "business" || newRole === "merchant"} /></label>
      </div>
      <button className="button primary" disabled={working}>Create member & account</button>
    </form>
    <div className="module-list-heading"><div><span className="eyebrow">MEMBER DIRECTORY</span><h3>Access and account status</h3></div><span>{filtered.length} of {rows.length}</span></div>
    <ModuleRecordToolbar search={search} onSearch={setSearch} placeholder="Search name or email" filter={roleFilter} onFilter={setRoleFilter} options={[{value:"all",label:"All roles"},...memberRoles.map((role) => ({value:role,label:role[0].toUpperCase()+role.slice(1)}))]} />
    {query.isLoading ? <div className="panel"><p className="muted">Loading member directory…</p></div> : <ModuleDataTable rows={filtered} empty="No members match those filters." columns={[
      {key:"member",label:"Member",render:(member) => <><b>{member.full_name}</b><small className="member-email">{member.email}</small></>},
      {key:"role",label:"Role",render:(member) => <StatePill value={member.role} />},
      {key:"accounts",label:"Accounts",render:(member) => member.account_count},
      {key:"kyc",label:"KYC",render:(member) => <StatePill value={member.kyc_status} />},
      {key:"access",label:"Access",render:(member) => <div className="member-access-action"><StatePill value={member.is_active ? "active" : "suspended"} /><button className="text-link" type="button" disabled={working} onClick={() => void perform(() => api(`/admin/members/${member.id}/status`, {method:"PATCH",body:JSON.stringify({is_active:!member.is_active})}), `Member access ${member.is_active ? "suspended" : "restored"}.`)}>{member.is_active ? "Suspend" : "Restore"}</button></div>},
    ]} />}
  </>;
}
