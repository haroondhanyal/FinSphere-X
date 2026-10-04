"use client";

import { api } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import { IssueCard, LimitEditor } from "../screen-actions";
import type { CustomerScreenProps } from "./types";

export function CardsScreen(props: CustomerScreenProps) {
  const { cardData, accountData, error, success, run } = props;
  return (
    <>
      <PageTitle
        eyebrow="CARD MANAGEMENT"
        title="Cards"
        copy="Issue a virtual or debit card and manage its status and daily limit."
      />
      <Notice error={error} success={success} />
      <div className="cards-grid">
        {cardData.map((card) => (
          <article className="bank-card" key={card.id}>
            <div className="card-brand">
              FinSphere<span>X</span>
            </div>
            <span className="card-chip" />
            <strong>•••• &nbsp;•••• &nbsp;•••• &nbsp;{card.last4}</strong>
            <div className="card-bottom">
              <span>
                FINSPHERE CUSTOMER
                <small>{card.card_type.toUpperCase()}</small>
              </span>
              <StatePill value={card.status} />
            </div>
          </article>
        ))}
      </div>
      <div className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">CARD CONTROLS</span>
            <h3>Manage your cards</h3>
          </div>
          <IssueCard
            accounts={accountData}
            onIssue={(account_id) =>
              run(
                () =>
                  api("/cards", {
                    method: "POST",
                    body: JSON.stringify({
                      account_id,
                      card_type: "virtual",
                    }),
                  }),
                "Virtual card issued and ready to activate.",
              )
            }
          />
        </div>
        {cardData.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Card</th>
                  <th>Type</th>
                  <th>Daily limit</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cardData.map((c) => (
                  <tr key={c.id}>
                    <td>{c.masked_number}</td>
                    <td>{c.card_type}</td>
                    <td>
                      <LimitEditor
                        value={c.daily_limit}
                        onSave={(daily_limit) =>
                          run(
                            () =>
                              api(`/cards/${c.id}/limit`, {
                                method: "PATCH",
                                body: JSON.stringify({ daily_limit }),
                              }),
                            "Daily card limit updated.",
                          )
                        }
                      />
                    </td>
                    <td>
                      <StatePill value={c.status} />
                    </td>
                    <td>
                      <div className="inline-actions">
                        {c.status === "inactive" && (
                          <button
                            onClick={() =>
                              run(
                                () =>
                                  api(`/cards/${c.id}/activate`, {
                                    method: "POST",
                                  }),
                                "Card activated.",
                              )
                            }
                          >
                            Activate
                          </button>
                        )}
                        {c.status === "active" && (
                          <button
                            onClick={() =>
                              run(
                                () =>
                                  api(`/cards/${c.id}/freeze`, {
                                    method: "POST",
                                  }),
                                "Card frozen.",
                              )
                            }
                          >
                            Freeze
                          </button>
                        )}
                        {c.status === "frozen" && (
                          <button
                            onClick={() =>
                              run(
                                () =>
                                  api(`/cards/${c.id}/unfreeze`, {
                                    method: "POST",
                                  }),
                                "Card unfrozen.",
                              )
                            }
                          >
                            Unfreeze
                          </button>
                        )}
                        {c.status !== "blocked" && (
                          <button
                            className="danger-link"
                            onClick={() =>
                              run(
                                () =>
                                  api(`/cards/${c.id}/block`, {
                                    method: "POST",
                                  }),
                                "Card blocked.",
                              )
                            }
                          >
                            Block
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="You have no cards yet. Issue a virtual card to get started." />
        )}
      </div>
    </>
  );
}
