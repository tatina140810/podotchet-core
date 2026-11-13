import type { Status } from "../api/types";
import { useI18n } from "../i18n";

export function StatusBadge({ status }: { status: Status }) {
  const { t } = useI18n();
  return <span className={`badge ${status}`}>{t(`status_${status}`)}</span>;
}
