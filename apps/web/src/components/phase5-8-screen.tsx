"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

import type {
  Bnpl,
  KycCase,
  Loan,
  LoanProduct,
} from "./phase5-8-screens/domain-types";
import { RoleDashboardScreen } from "./phase5-8-screens/role-dashboard-screen";
import { LoansScreen } from "./phase5-8-screens/loans-screen";
import { BnplScreen } from "./phase5-8-screens/bnpl-screen";
import { CollectionsScreen } from "./phase5-8-screens/collections-screen";
import { BusinessScreen } from "./phase5-8-screens/business-screen";
import { BusinessReviewScreen } from "./phase5-8-screens/business-review-screen";
import { PayrollScreen } from "./phase5-8-screens/payroll-screen";
import { PayrollReviewScreen } from "./phase5-8-screens/payroll-review-screen";
import { ExpensesScreen } from "./phase5-8-screens/expenses-screen";
import { ExpenseReviewScreen } from "./phase5-8-screens/expense-review-screen";
import { SettlementReviewScreen } from "./phase5-8-screens/settlement-review-screen";
import { MerchantScreen } from "./phase5-8-screens/merchant-screen";
import { MerchantTransactionsScreen } from "./phase5-8-screens/merchant-transactions-screen";
import { MerchantDisputesScreen } from "./phase5-8-screens/merchant-disputes-screen";
import { FinanceScreen } from "./phase5-8-screens/finance-screen";
import { RiskCaseworkScreen } from "./phase5-8-screens/risk-casework-screen";
import { MembersScreen } from "./phase5-8-screens/members-screen";

export function Phase58Screen({ section }: { section: string }) {
  const cache = useQueryClient();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [working, setWorking] = useState(false);
  const query = useQuery<unknown>({
    queryKey: ["phase58", section],
    queryFn: async () => {
      if (section === "loans") {
        const [data, products] = await Promise.all([
          api<{
            applications: Loan[];
            can_review: boolean;
            can_manage_products: boolean;
          }>("/loans/applications"),
          api<LoanProduct[]>("/loans/products"),
        ]);
        const applications = await Promise.all(
          data.applications.map(async (loan) => {
            try {
              const schedule = await api<{
                installments: NonNullable<Loan["installments"]>;
              }>(`/loans/applications/${loan.id}/schedule`);
              return { ...loan, installments: schedule.installments };
            } catch {
              return loan;
            }
          }),
        );
        return { ...data, applications, products };
      }
      if (section === "bnpl") return api<Bnpl[]>("/bnpl/plans");
      if (section === "collections") {
        const [loans, bnpl] = await Promise.all([
          api<
            {
              id: number;
              loan_id: number;
              installment_number: number;
              due_at: string;
              amount: string;
              status: string;
            }[]
          >("/loans/collections"),
          api<
            {
              id: number;
              plan_id: number;
              installment_number: number;
              due_at: string;
              amount: string;
              status: string;
            }[]
          >("/bnpl/collections"),
        ]);
        return { loans, bnpl };
      }
      if (section === "business") {
        const [profile, invoices, payroll, expenses] = await Promise.all([
          api<{ id: number; legal_name: string; status: string }>(
            "/business/organizations/me",
          ).catch(() => null),
          api<
            {
              id: number;
              invoice_number: string;
              customer_name: string;
              amount: string;
              currency: string;
              status: string;
            }[]
          >("/business/invoices").catch(() => []),
          api<
            {
              id: number;
              pay_period: string;
              employee_count: number;
              total_amount: string;
              currency: string;
              status: string;
            }[]
          >("/business/payroll").catch(() => []),
          api<
            {
              id: number;
              claimant_name: string;
              description: string;
              amount: string;
              currency: string;
              evidence_reference: string;
              status: string;
            }[]
          >("/business/expenses").catch(() => []),
        ]);
        return { profile, invoices, payroll, expenses };
      }
      if (section === "business-dashboard")
        return api<Record<string, string | number>>("/business/summary");
      if (section === "merchant-dashboard")
        return api<Record<string, string | number>>("/merchant/summary");
      if (section === "operations-dashboard" || section === "admin-dashboard")
        return api<Record<string, number>>("/operations/summary");
      if (section === "business-review")
        return api<
          { id: number; user_id: number; legal_name: string; status: string }[]
        >("/business/organizations");
      if (section === "payroll")
        return api<
          {
            id: number;
            pay_period: string;
            employee_count: number;
            total_amount: string;
            currency: string;
            status: string;
          }[]
        >("/business/payroll");
      if (section === "expenses")
        return api<
          {
            id: number;
            claimant_name: string;
            description: string;
            amount: string;
            currency: string;
            evidence_reference: string;
            status: string;
          }[]
        >("/business/expenses");
      if (section === "expense-review")
        return api<
          {
            id: number;
            organization_id: number;
            claimant_name: string;
            description: string;
            amount: string;
            currency: string;
            evidence_reference: string;
          }[]
        >("/business/expenses/review");
      if (section === "payroll-review")
        return api<
          {
            id: number;
            organization_id: number;
            pay_period: string;
            employee_count: number;
            total_amount: string;
            currency: string;
          }[]
        >("/business/payroll/review");
      if (section === "settlement-review")
        return api<
          {
            id: number;
            organization_id: number;
            reference: string;
            gross_amount: string;
            fee_amount: string;
            net_amount: string;
            currency: string;
          }[]
        >("/merchant/settlements/review");
      if (section === "merchant-transactions")
        return api<
          {
            id: number;
            reference: string;
            description: string;
            amount: string;
            currency: string;
            status: string;
          }[]
        >("/merchant/sales");
      if (section === "merchant-disputes")
        return api<{
          items: {
            id: number;
            sale_id: number;
            sale_reference: string;
            sale_description: string;
            sale_amount: string;
            currency: string;
            organization_id: number;
            reason: string;
            evidence_reference: string;
            status: string;
            decision: string;
            decision_note: string;
            created_at: string;
          }[];
          can_review: boolean;
          available_sales: { id: number; reference: string; description: string; amount: string; currency: string }[];
        }>("/merchant/disputes");
      if (section === "members") return api<Record<string, unknown>[]>("/admin/members");
      if (section === "merchant")
        return api<
          {
            id: number;
            reference: string;
            gross_amount: string;
            fee_amount: string;
            net_amount: string;
            currency: string;
            status: string;
            disclosure: string;
          }[]
        >("/merchant/settlements");
      if (section === "finance") {
        const [trial, runs, fees, journals] = await Promise.all([
          api<{
            accounts: {
              code: string;
              name: string;
              currency: string;
              debit: string;
              credit: string;
            }[];
            debit_total: string;
            credit_total: string;
            balanced: boolean;
          }>("/finance/trial-balance"),
          api<
            {
              id: number;
              source: string;
              ledger_total: string;
              external_total: string;
              status: string;
              notes: string;
            }[]
          >("/finance/reconciliation-runs"),
          api<
            {
              id: number;
              code: string;
              description: string;
              percentage: string;
              active: boolean;
            }[]
          >("/finance/fee-rules"),
          api<
            {
              id: number;
              reference: string;
              transaction_id: number;
              lines: {
                account_code: string;
                account_name: string;
                debit: string;
                credit: string;
              }[];
            }[]
          >("/finance/journals"),
        ]);
        return { trial, runs, fees, journals };
      }
      if (section === "risk") {
        const [cases, screenings] = await Promise.all([
          api<KycCase[]>("/risk/cases"),
          api<
            {
              id: number;
              subject_name: string;
              category: string;
              score: number;
              result: string;
              rationale: string;
            }[]
          >("/risk/screenings"),
        ]);
        return { cases, screenings };
      }
      return api<KycCase[]>("/risk/cases");
    },
  });
  const perform = async (action: () => Promise<unknown>, message: string): Promise<boolean> => {
    setWorking(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(message);
      await cache.invalidateQueries({ queryKey: ["phase58"] });
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Action failed");
      return false;
    } finally {
      setWorking(false);
    }
  };
  const submit =
    (handler: (data: FormData) => Promise<unknown>, message: string) =>
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const element = event.currentTarget;
      const data = new FormData(element);
      void perform(() => handler(data), message).then((saved) => { if (saved) element.reset(); });
    };

  const screenProps = {
    section,
    query,
    working,
    error,
    notice,
    perform,
    submit,
  };

  if (section.endsWith("-dashboard"))
    return <RoleDashboardScreen {...screenProps} />;

  if (section === "loans") return <LoansScreen {...screenProps} />;

  if (section === "bnpl") return <BnplScreen {...screenProps} />;

  if (section === "collections") return <CollectionsScreen {...screenProps} />;

  if (section === "business") return <BusinessScreen {...screenProps} />;

  if (section === "business-review")
    return <BusinessReviewScreen {...screenProps} />;

  if (section === "payroll") return <PayrollScreen {...screenProps} />;

  if (section === "payroll-review")
    return <PayrollReviewScreen {...screenProps} />;

  if (section === "expenses") return <ExpensesScreen {...screenProps} />;

  if (section === "expense-review")
    return <ExpenseReviewScreen {...screenProps} />;

  if (section === "settlement-review")
    return <SettlementReviewScreen {...screenProps} />;

  if (section === "merchant") return <MerchantScreen {...screenProps} />;

  if (section === "merchant-transactions")
    return <MerchantTransactionsScreen {...screenProps} />;

  if (section === "merchant-disputes")
    return <MerchantDisputesScreen {...screenProps} />;

  if (section === "members") return <MembersScreen {...screenProps} />;

  if (section === "finance") return <FinanceScreen {...screenProps} />;

  return <RiskCaseworkScreen {...screenProps} />;
}
