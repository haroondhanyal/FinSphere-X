"use client";

import { api, money } from "@/lib/api";
import { Empty, PageTitle, StatePill } from "../screen-primitives";
import type { Phase911ScreenProps } from "./types";

type Position = {
  id: number;
  product_name: string;
  principal: string;
  illustrative_value: string;
  currency: string;
  status: string;
};

export function InvestmentsScreen(props: Phase911ScreenProps) {
  const { query, busy, notice, form } = props;
  const data = query.data as
    | {
        products: {
          code: string;
          name: string;
          description: string;
          annual_yield: string;
          minimum_amount: string;
          currency: string;
        }[];
        portfolio: { positions: Position[]; disclosure: string };
      }
    | undefined;
  return (
    <>
      <PageTitle
        eyebrow="PHASE 9 · INVESTMENTS"
        title="Portfolio"
        copy="Explore illustrative products and record a sample position."
      />
      {notice}
      <div className="two-column">
        <form
          className="panel form-stack"
          onSubmit={form(
            (d) =>
              api("/investments/positions", {
                method: "POST",
                body: JSON.stringify({
                  product_code: d.get("product_code"),
                  amount: d.get("amount"),
                }),
              }),
            "Demo investment position created.",
          )}
        >
          <h3>Record sample position</h3>
          <label>
            Product
            <select name="product_code">
              {(data?.products ?? []).map((product) => (
                <option value={product.code} key={product.code}>
                  {product.name} · illustrative {product.annual_yield}%
                </option>
              ))}
            </select>
          </label>
          <label>
            Amount
            <input type="number" min="1" step="0.01" name="amount" required />
          </label>
          <button disabled={busy}>Add position</button>
          <p className="form-hint">
            No investment purchase or market pricing occurs.
          </p>
        </form>
        <div className="panel">
          <h3>Available products</h3>
          {data?.products.map((product) => (
            <div className="beneficiary-row" key={product.code}>
              <span>
                <b>{product.name}</b>
                <small>
                  {product.description} · minimum{" "}
                  {money(product.minimum_amount, product.currency)}
                </small>
              </span>
              <StatePill value={`${product.annual_yield}% indicative`} />
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <h3>Your portfolio</h3>
        {data?.portfolio.positions.length ? (
          data.portfolio.positions.map((position) => (
            <div className="beneficiary-row" key={position.id}>
              <span>
                <b>{position.product_name}</b>
                <small>
                  Principal {money(position.principal, position.currency)} ·
                  illustrative value{" "}
                  {money(position.illustrative_value, position.currency)}
                </small>
              </span>
              <StatePill value={position.status} />
            </div>
          ))
        ) : (
          <Empty text="No portfolio positions." />
        )}
        <p className="form-hint">{data?.portfolio.disclosure}</p>
      </div>
    </>
  );
}
