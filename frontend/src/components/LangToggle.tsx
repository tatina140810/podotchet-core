import { useI18n, type Lang } from "../i18n";

export function LangToggle() {
  const { lang, setLang } = useI18n();
  return (
    <div className="seg">
      {(["en", "ru"] as Lang[]).map((l) => (
        <button key={l} className={l === lang ? "on" : ""} onClick={() => setLang(l)}>
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
