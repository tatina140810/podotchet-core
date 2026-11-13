import { useState } from "react";
import { Download, Lock } from "lucide-react";
import { useReport } from "../api/hooks";
import { download } from "../api/client";
import { BarList } from "../components/BarList";
import { useAuth } from "../lib/auth";
import { isoToday, money } from "../lib/format";
import { useI18n } from "../i18n";

const sixMonthsAgo = () => {
  const d = new Date();
  d.setMonth(d.getMonth() - 5, 1);
  return d.toISOString().slice(0, 10);
};

export default function Reports() {
  const { me } = useAuth();
  const { t, lang } = useI18n();
  const [from, setFrom] = useState(sixMonthsAgo);
  const [to, setTo] = useState(isoToday);
  const { data } = useReport(from, to);
  const canExport = !!me?.plan_limits.can_export;
  const cur = data?.currency ?? "USD";

  return (
    <>
      <header className="page-head">
        <h1>{t("navReports")}</h1>
        <div className="filters">
          <label>
            {t("from")}
            <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label>
            {t("to")}
            <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
          <button
            disabled={!canExport}
            title={canExport ? undefined : t("upgradeRequired")}
            onClick={() => download(`/api/reports/expenses.csv?from=${from}&to=${to}`, `expenses_${from}_${to}.csv`)}
          >
            {canExport ? <Download size={16} /> : <Lock size={16} />} {t("exportCsv")}
          </button>
        </div>
      </header>
      {data && (
        <>
          <div className="card total">
            <span className="muted">{t("total")}</span>
            <strong>{money(data.total, cur, lang)}</strong>
          </div>
          <div className="grid-3">
            <section className="card">
              <h2>{t("byCategory")}</h2>
              <BarList rows={data.by_category} currency={cur} />
            </section>
            <section className="card">
              <h2>{t("byEmployee")}</h2>
              <BarList rows={data.by_employee} currency={cur} />
            </section>
            <section className="card">
              <h2>{t("byMonth")}</h2>
              <BarList rows={data.by_month} currency={cur} />
            </section>
          </div>
        </>
      )}
    </>
  );
}
