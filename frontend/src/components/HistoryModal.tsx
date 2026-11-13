import { useHistory } from "../api/hooks";
import { useI18n } from "../i18n";
import { Modal } from "./Modal";

const fmt = (v: unknown) => (v === null || v === undefined || v === "" ? "—" : String(v));

export function HistoryModal({ id, onClose }: { id: number; onClose: () => void }) {
  const { t, lang } = useI18n();
  const { data = [] } = useHistory(id);
  return (
    <Modal title={`${t("history")} #${id}`} onClose={onClose}>
      {!data.length && <p className="muted">{t("noData")}</p>}
      <ol className="timeline">
        {data.map((c, i) => (
          <li key={i}>
            <div className="small muted">
              {new Date(c.changed_at).toLocaleString(lang === "ru" ? "ru-RU" : "en-US")}
            </div>
            <div>
              <strong>{c.changed_by}</strong> {t(`action_${c.action}`)}
            </div>
            {c.action !== "delete" &&
              Object.entries(c.diff).map(([field, d]) => (
                <div key={field} className="small diff">
                  <code>{field}</code> {fmt(d.old)} → {fmt(d.new)}
                </div>
              ))}
          </li>
        ))}
      </ol>
    </Modal>
  );
}
