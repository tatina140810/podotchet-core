import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { Wallet } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useI18n } from "../i18n";
import { LangToggle } from "../components/LangToggle";

export default function Login() {
  const { me, login } = useAuth();
  const { t } = useI18n();
  const [email, setEmail] = useState("admin@acme.test");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  if (me) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(false);
    try {
      await login(email, password);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <form className="card login" onSubmit={submit}>
        <div className="brand big">
          <Wallet size={28} />
          <span>{t("appName")}</span>
        </div>
        <p className="muted">{t("tagline")}</p>
        <label>
          {t("email")}
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          {t("password")}
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <p className="error">{t("invalidLogin")}</p>}
        <button type="submit" disabled={busy}>
          {t("signIn")}
        </button>
        <div className="login-foot">
          <span className="small muted">{t("demoHint")}</span>
          <LangToggle />
        </div>
      </form>
    </div>
  );
}
