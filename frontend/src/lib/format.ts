export function money(amount: string | number, currency: string, lang: string): string {
  return new Intl.NumberFormat(lang === "ru" ? "ru-RU" : "en-US", { style: "currency", currency }).format(
    Number(amount),
  );
}

export function day(iso: string, lang: string): string {
  return new Date(`${iso.slice(0, 10)}T00:00:00`).toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export const isoToday = () => new Date().toISOString().slice(0, 10);
