import { useState } from "react";
import { History, Pencil, Plus, Trash2 } from "lucide-react";
import { useDeleteExpense, useMyExpenses } from "../api/hooks";
import type { Expense } from "../api/types";
import { ExpenseForm } from "../components/ExpenseForm";
import { HistoryModal } from "../components/HistoryModal";
import { StatusBadge } from "../components/StatusBadge";
import { day, money } from "../lib/format";
import { useI18n } from "../i18n";

const editable = (e: Expense) => e.status !== "approved";

export default function MyExpenses() {
  const { t, lang } = useI18n();
  const { data = [] } = useMyExpenses();
  const del = useDeleteExpense();
  const [editing, setEditing] = useState<Expense | "new" | null>(null);
  const [historyId, setHistoryId] = useState<number | null>(null);

  return (
    <>
      <header className="page-head">
        <h1>{t("navMyExpenses")}</h1>
        <button onClick={() => setEditing("new")}>
          <Plus size={16} /> {t("newExpense")}
        </button>
      </header>
      <section className="card table-card">
        {!data.length && <p className="muted">{t("noData")}</p>}
        <table>
          <thead>
            <tr>
              <th>{t("date")}</th>
              <th>{t("category")}</th>
              <th>{t("description")}</th>
              <th className="num">{t("amount")}</th>
              <th>{t("status")}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.map((e) => (
              <tr key={e.id}>
                <td>{day(e.spent_on, lang)}</td>
                <td>{e.category_name}</td>
                <td>
                  {e.description}
                  {e.review_comment && <div className="small danger-text">{e.review_comment}</div>}
                </td>
                <td className="num">{money(e.amount, e.currency, lang)}</td>
                <td>
                  <StatusBadge status={e.status} />
                </td>
                <td className="row-actions">
                  <button className="icon-btn ghost" title={t("history")} onClick={() => setHistoryId(e.id)}>
                    <History size={15} />
                  </button>
                  {editable(e) && (
                    <>
                      <button className="icon-btn ghost" title={t("save")} onClick={() => setEditing(e)}>
                        <Pencil size={15} />
                      </button>
                      <button className="icon-btn ghost" title={t("delete")} onClick={() => del.mutate(e.id)}>
                        <Trash2 size={15} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {editing && <ExpenseForm expense={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} />}
      {historyId !== null && <HistoryModal id={historyId} onClose={() => setHistoryId(null)} />}
    </>
  );
}
