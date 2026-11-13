import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, CheckSquare, LayoutDashboard, LogOut, Receipt, Wallet } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useI18n } from "../i18n";
import { LangToggle } from "./LangToggle";

export function Layout() {
  const { me, can, logout } = useAuth();
  const { t } = useI18n();
  const links = [
    { to: "/", icon: LayoutDashboard, label: t("navDashboard"), show: true },
    { to: "/expenses", icon: Receipt, label: t("navMyExpenses"), show: can("submit_expense") },
    { to: "/approvals", icon: CheckSquare, label: t("navApprovals"), show: can("review_expense") },
    { to: "/reports", icon: BarChart3, label: t("navReports"), show: can("view_reports") },
  ];
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <Wallet size={22} />
          <span>{t("appName")}</span>
        </div>
        <nav>
          {links
            .filter((l) => l.show)
            .map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} end={to === "/"}>
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
        </nav>
        <div className="sidebar-foot">
          <div className="small">{me?.full_name}</div>
          <div className="small muted">
            {me?.org_name} · {me?.role} · {t("plan")} {me?.plan}
          </div>
          <div className="foot-actions">
            <LangToggle />
            <button className="ghost icon-btn" onClick={logout} title={t("signOut")}>
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
