import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { useDashboard } from "../api/hooks";
import { BarList } from "../components/BarList";
import { Stat } from "../components/Stat";
import { useAuth } from "../lib/auth";
import { money } from "../lib/format";
import { useI18n } from "../i18n";

export default function Dashboard() {
  const { me } = useAuth();
  const { t, lang } = useI18n();
  const { data } = useDashboard();
  if (!data) return null;
  const cur = data.currency;
  return (
    <>
      <header className="page-head">
        <h1>{t("navDashboard")}</h1>
        <span className="muted">{me?.org_name}</span>
      </header>
      <div className="stats">
        <Stat icon={CheckCircle2} label={t("approvedThisMonth")} value={money(data.approved_this_month, cur, lang)} />
        <Stat
          icon={Clock}
          tone="warning"
          label={t("awaitingApproval")}
          value={money(data.pending_total, cur, lang)}
          hint={`${data.pending_count} ${t("items")}`}
        />
        <Stat icon={XCircle} tone="danger" label={t("rejected")} value={String(data.rejected_count)} />
      </div>
      <section className="card">
        <h2>{t("topCategories")}</h2>
        <BarList rows={data.by_category} currency={cur} />
      </section>
    </>
  );
}
