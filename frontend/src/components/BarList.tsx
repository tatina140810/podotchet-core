import type { Row } from "../api/types";
import { money } from "../lib/format";
import { useI18n } from "../i18n";

export function BarList({ rows, currency }: { rows: Row[]; currency: string }) {
  const { t, lang } = useI18n();
  if (!rows.length) return <p className="muted">{t("noData")}</p>;
  const max = Math.max(...rows.map((r) => Number(r.total)));
  return (
    <ul className="bars">
      {rows.map((r) => (
        <li key={r.key}>
          <div className="bar-head">
            <span>{r.key}</span>
            <strong>{money(r.total, currency, lang)}</strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(Number(r.total) / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}
