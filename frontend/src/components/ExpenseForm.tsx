import { useState, type FormEvent } from "react";
import { useCategories, useSaveExpense } from "../api/hooks";
import type { Expense } from "../api/types";
import { useI18n } from "../i18n";
import { isoToday } from "../lib/format";
import { Modal } from "./Modal";

export function ExpenseForm({ expense, onClose }: { expense?: Expense; onClose: () => void }) {
  const { t } = useI18n();
  const { data: categories = [] } = useCategories();
  const save = useSaveExpense();
  const [form, setForm] = useState({
    category_id: expense?.category_id ?? 0,
    amount: expense?.amount ?? "",
    spent_on: expense?.spent_on ?? isoToday(),
    description: expense?.description ?? "",
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: k === "category_id" ? Number(e.target.value) : e.target.value });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate({ id: expense?.id, body: form }, { onSuccess: onClose });
  };

  return (
    <Modal title={expense ? `#${expense.id}` : t("newExpense")} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          {t("category")}
          <select required value={form.category_id || ""} onChange={set("category_id")}>
            <option value="" disabled />
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <div className="row-2">
          <label>
            {t("amount")}
            <input required type="number" min="0.01" step="0.01" value={form.amount} onChange={set("amount")} />
          </label>
          <label>
            {t("date")}
            <input required type="date" value={form.spent_on} onChange={set("spent_on")} />
          </label>
        </div>
        <label>
          {t("description")}
          <textarea rows={3} value={form.description} onChange={set("description")} />
        </label>
        {save.error && <p className="error">{save.error.message}</p>}
        <div className="actions">
          <button type="button" className="ghost" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" disabled={save.isPending}>
            {t("save")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
