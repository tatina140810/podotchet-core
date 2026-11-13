import { useState } from "react";
import { Check, X } from "lucide-react";
import { useQueue, useReview } from "../api/hooks";
import type { Expense } from "../api/types";
import { Modal } from "../components/Modal";
import { day, money } from "../lib/format";
import { useI18n } from "../i18n";

export default function Approvals() {
  const { t, lang } = useI18n();
  const { data = [] } = useQueue();
  const review = useReview();
  const [rejecting, setRejecting] = useState<Expense | null>(null);
  const [reason, setReason] = useState("");

  const reject = () => {
    if (!rejecting) return;
    review.mutate(
      { id: rejecting.id, action: "reject", comment: reason },
      { onSuccess: () => (setRejecting(null), setReason("")) },
    );
  };

  return (
    <>
      <header className="page-head">
        <h1>{t("navApprovals")}</h1>
        <span className="muted">{data.length}</span>
      </header>
      {!data.length && <p className="card muted">{t("queueEmpty")}</p>}
      <div className="queue">
        {data.map((e) => (
          <article key={e.id} className="card queue-item">
            <div>
              <div className="queue-amount">{money(e.amount, e.currency, lang)}</div>
              <div>
                <strong>{e.employee_name}</strong> · {e.category_name}
              </div>
              <div className="muted small">
                {day(e.spent_on, lang)} · {e.description}
              </div>
            </div>
            <div className="queue-actions">
              <button className="ghost" onClick={() => setRejecting(e)}>
                <X size={16} /> {t("reject")}
              </button>
              <button className="success" onClick={() => review.mutate({ id: e.id, action: "approve" })}>
                <Check size={16} /> {t("approve")}
              </button>
            </div>
          </article>
        ))}
      </div>
      {rejecting && (
        <Modal title={`${t("reject")} #${rejecting.id}`} onClose={() => setRejecting(null)}>
          <label>
            {t("rejectReason")}
            <textarea rows={3} value={reason} onChange={(ev) => setReason(ev.target.value)} />
          </label>
          <div className="actions">
            <button className="ghost" onClick={() => setRejecting(null)}>
              {t("cancel")}
            </button>
            <button className="danger" disabled={!reason.trim()} onClick={reject}>
              {t("reject")}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
