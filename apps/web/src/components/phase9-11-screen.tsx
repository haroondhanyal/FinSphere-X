"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Notice } from "./screen-primitives";
import { InvestmentsScreen } from "./phase9-11-screens/investments-screen";
import { FxRemittanceScreen } from "./phase9-11-screens/fx-remittance-screen";
import { TreasuryScreen } from "./phase9-11-screens/treasury-screen";
import { RemittanceReviewScreen } from "./phase9-11-screens/remittance-review-screen";
import { CopilotScreen } from "./phase9-11-screens/copilot-screen";
import { OpenBankingScreen } from "./phase9-11-screens/open-banking-screen";
import { DeveloperPlatformScreen } from "./phase9-11-screens/developer-platform-screen";

type Position = {
  id: number;
  product_code: string;
  product_name: string;
  principal: string;
  illustrative_value: string;
  currency: string;
  status: string;
};

type Consent = {
  id: number;
  provider_name: string;
  scopes: string[];
  status: string;
  expires_at: string;
};

export function Phase911Screen({ section }: { section: string }) {
  const cache = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const query = useQuery<unknown>({
    queryKey: ["phase911", section],
    queryFn: async () => {
      if (section === "investments") {
        const [products, portfolio] = await Promise.all([
          api<
            {
              code: string;
              name: string;
              description: string;
              annual_yield: string;
              minimum_amount: string;
              currency: string;
            }[]
          >("/investments/products"),
          api<{ positions: Position[]; disclosure: string }>(
            "/investments/portfolio",
          ),
        ]);
        return { products, portfolio };
      }
      if (section === "fx-remittance") {
        const [accounts, remittances] = await Promise.all([
          api<
            {
              id: number;
              account_number_masked: string;
              currency: string;
              balance: string;
            }[]
          >("/accounts"),
          api<Record<string, unknown>[]>("/remittances"),
        ]);
        return { accounts, remittances };
      }
      if (section === "open-banking") {
        const [providers, consents] = await Promise.all([
          api<{ id: string; name: string; status: string }[]>(
            "/open-banking/providers",
          ),
          api<Consent[]>("/open-banking/consents"),
        ]);
        return { providers, consents };
      }
      if (section === "treasury")
        return api<{
          balances: { currency: string; total: string }[];
          source: string;
          as_of: string;
        }>("/treasury/liquidity");
      if (section === "remittance-review")
        return api<Record<string, unknown>[]>("/remittances");
      if (section === "developer") {
        const [clients, webhooks, deliveries] = await Promise.all([
          api<Record<string, unknown>[]>("/developer/clients"),
          api<Record<string, unknown>[]>("/developer/webhooks"),
          api<Record<string, unknown>[]>("/developer/webhooks/deliveries"),
        ]);
        return { clients, webhooks, deliveries };
      }
      if (section === "copilot") return api("/copilot/status");
      return null;
    },
  });

  const act = async (
    request: () => Promise<unknown>,
    success: string,
    refresh = true,
  ) => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await request();
      setResult(response);
      setMessage(success);
      if (refresh) await cache.invalidateQueries({ queryKey: ["phase911"] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  const form =
    (handler: (data: FormData) => Promise<unknown>, success: string) =>
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const element = event.currentTarget;
      const data = new FormData(element);
      void act(() => handler(data), success).then(() => element.reset());
    };

  const notice = (
    <Notice
      error={error || (query.error instanceof Error ? query.error.message : "")}
      success={message}
    />
  );
  const screenProps = { query, busy, result, notice, form, act };

  if (section === "investments") return <InvestmentsScreen {...screenProps} />;
  if (section === "fx-remittance")
    return <FxRemittanceScreen {...screenProps} />;
  if (section === "treasury") return <TreasuryScreen {...screenProps} />;
  if (section === "remittance-review")
    return <RemittanceReviewScreen {...screenProps} />;
  if (section === "copilot") return <CopilotScreen {...screenProps} />;
  if (section === "open-banking") return <OpenBankingScreen {...screenProps} />;
  return <DeveloperPlatformScreen {...screenProps} />;
}
