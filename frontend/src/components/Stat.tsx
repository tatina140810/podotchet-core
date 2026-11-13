import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
  tone?: "accent" | "warning" | "danger";
}

export function Stat({ icon: Icon, label, value, hint, tone = "accent" }: Props) {
  return (
    <div className="card stat">
      <div className={`stat-icon ${tone}`}>
        <Icon size={18} />
      </div>
      <div>
        <div className="muted small">{label}</div>
        <div className="stat-value">{value}</div>
        {hint && <div className="muted small">{hint}</div>}
      </div>
    </div>
  );
}
