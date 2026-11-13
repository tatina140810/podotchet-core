import { createContext, useContext, useState, type ReactNode } from "react";
import { en, type Dict } from "./en";
import { ru } from "./ru";

export type Lang = "en" | "ru";
const DICTS: Record<Lang, Dict> = { en, ru };
const STORAGE_KEY = "pc_lang";

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "ru") return saved;
  } catch {
    /* storage unavailable */
  }
  return "en";
}

interface Ctx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: keyof Dict) => string;
}

const I18nContext = createContext<Ctx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* ignore */
    }
  };
  const t = (key: keyof Dict) => DICTS[lang][key];
  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): Ctx {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n outside I18nProvider");
  return ctx;
}
