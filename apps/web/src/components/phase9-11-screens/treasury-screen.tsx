"use client";

import { money } from "@/lib/api";
import { PageTitle } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

export function TreasuryScreen(props: Phase911ScreenProps) {
  const { query, notice } = props;
  const data = query.data as
    | {
        balances: { currency: string; total: string }[];
        source: string;
        as_of: string;
      }
    | undefined;
  return (
    <>
      <PageTitle
        eyebrow="PHASE 9 · TREASURY"
        title="Liquidity overview"
        copy="Aggregate local account balances by currency."
      />
      {notice}
      <div className="panel-grid">
        {data?.balances.map((row) => (
          <div className="panel" key={row.currency}>
            <span className="eyebrow">{row.currency} LIQUIDITY</span>
            <h3>{money(row.total, row.currency)}</h3>
          </div>
        ))}
      </div>
      <p className="form-hint">
        {data?.source} · {data?.as_of}
      </p>
    </>
  );
}
