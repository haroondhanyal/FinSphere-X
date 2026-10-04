"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { api, sumMoneyAmounts } from "@/lib/api";
import {
  type Account,
  type Beneficiary,
  type Card,
  type Profile,
  type Transaction,
} from "./screen-types";
import { PageTitle } from "./screen-primitives";
import { AccountDetailScreen } from "./account-detail-screen";
import { StatementScreen } from "./statements-screen";
import { Phase58Screen } from "./phase5-8-screen";
import { Phase911Screen } from "./phase9-11-screen";
import { DashboardScreen } from "./customer-screens/dashboard-screen";
import { AccountsScreen } from "./customer-screens/accounts-screen";
import { WalletScreen } from "./customer-screens/wallet-screen";
import { TransferScreen } from "./customer-screens/transfer-screen";
import { CardsScreen } from "./customer-screens/cards-screen";
import { KycQueueScreen } from "./customer-screens/kyc-queue-screen";
import { ProfileSecurityScreen } from "./customer-screens/profile-security-screen";
import { WorkspaceUtilityScreen } from "./workspace-utility-screen";

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
  const viewerQuery = useQuery({
    queryKey: ["viewer"],
    queryFn: () => api<{ role: string }>("/auth/me"),
    enabled: pathname === "/dashboard",
  });
  const kycQueueQuery = useQuery({
    queryKey: ["kyc-queue"],
    queryFn: () =>
      api<{ id: number; full_name: string; email?: string; kyc_status: string; document_count?: number }[]>(
        "/customers/",
      ),
    enabled: pathname === "/kyc",
  });
  const accountData = accountQuery.data ?? [];
  const beneficiaryData = beneficiariesQuery.data ?? [];
  const transactionData = transactionsQuery.data ?? [];
  const cardData = cardsQuery.data ?? [];
  const walletData = walletQuery.data;
  const profileData = profileQuery.data;
  const kycQueue = kycQueueQuery.data ?? [];
  const balance = sumMoneyAmounts(
    accountData.map((account) => account.balance),
  );

  const phase58Section = pathname.slice(1);
  if (["onboarding", "support", "notifications", "budgets", "goals", "deposits"].includes(phase58Section))
    return <WorkspaceUtilityScreen section={phase58Section} />;
  if (
    [
      "loans",
      "bnpl",
      "collections",
      "business",
      "business-review",
      "payroll",
      "payroll-review",
      "expenses",
      "expense-review",
      "merchant",
      "merchant-transactions",
      "merchant-disputes",
      "members",
      "settlement-review",
      "finance",
      "risk",
    ].includes(phase58Section)
  )
    return <Phase58Screen section={phase58Section} />;
  if (
    [
      "investments",
      "fx-remittance",
      "copilot",
      "open-banking",
      "treasury",
      "remittance-review",
      "developer",
    ].includes(phase58Section)
  )
    return <Phase911Screen section={phase58Section} />;
  if (
    pathname === "/dashboard" &&
    viewerQuery.data?.role &&
    viewerQuery.data.role !== "customer"
  )
    return <Phase58Screen section={`${viewerQuery.data.role}-dashboard`} />;

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

  const screenProps = {
    pathname,
    accountData,
    beneficiaryData,
    transactionData,
    cardData,
    walletData,
    profileData,
    kycQueue,
    balance,
    error,
    success,
    accountQuery,
    walletQuery,
    cardsQuery,
    transactionsQuery,
    kycQueueQuery,
    run,
  };

  if (pathname === "/dashboard") return <DashboardScreen {...screenProps} />;

  if (pathname.startsWith("/accounts/") && pathname !== "/accounts/")
    return <AccountDetailScreen accountId={Number(pathname.split("/")[2])} />;

  if (pathname === "/accounts") return <AccountsScreen {...screenProps} />;

  if (pathname === "/wallet") return <WalletScreen {...screenProps} />;

  if (pathname === "/transfers" || pathname === "/payments")
    return <TransferScreen {...screenProps} />;

  if (pathname === "/cards") return <CardsScreen {...screenProps} />;

  if (pathname === "/statements")
    return <StatementScreen accounts={accountData} />;

  if (pathname === "/kyc") return <KycQueueScreen {...screenProps} />;

  if (pathname === "/profile" || pathname === "/security")
    return <ProfileSecurityScreen {...screenProps} />;

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
