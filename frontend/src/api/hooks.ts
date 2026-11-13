import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { Category, Change, Dashboard, Expense, Me, Report } from "./types";

const MIN = 60_000;

export const useMe = (enabled: boolean) =>
  useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/api/auth/me"), enabled, retry: false });

// Reference data changes rarely: cache it for 10 minutes.
export const useCategories = () =>
  useQuery({ queryKey: ["categories"], queryFn: () => api<Category[]>("/api/categories"), staleTime: 10 * MIN });

// Money that is waiting for a decision must always be fresh.
export const useMyExpenses = () =>
  useQuery({ queryKey: ["expenses", "mine"], queryFn: () => api<Expense[]>("/api/expenses?mine=true"), staleTime: 0 });

export const useQueue = () =>
  useQuery({ queryKey: ["approvals"], queryFn: () => api<Expense[]>("/api/approvals"), staleTime: 0 });

export const useDashboard = () =>
  useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dashboard>("/api/dashboard"), staleTime: 0 });

export const useReport = (from: string, to: string) =>
  useQuery({
    queryKey: ["report", from, to],
    queryFn: () => api<Report>(`/api/reports?from=${from}&to=${to}`),
    staleTime: MIN,
  });

export const useHistory = (id: number | null) =>
  useQuery({
    queryKey: ["history", id],
    queryFn: () => api<Change[]>(`/api/expenses/${id}/history`),
    enabled: id !== null,
  });

function useInvalidateMoney() {
  const qc = useQueryClient();
  return () =>
    ["expenses", "approvals", "dashboard", "report", "history"].forEach((k) =>
      qc.invalidateQueries({ queryKey: [k] }),
    );
}

export interface ExpenseInput {
  category_id: number;
  amount: string;
  spent_on: string;
  description: string;
}

export function useSaveExpense() {
  const done = useInvalidateMoney();
  return useMutation({
    mutationFn: ({ id, body }: { id?: number; body: ExpenseInput }) =>
      id
        ? api<Expense>(`/api/expenses/${id}`, { method: "PATCH", body: JSON.stringify(body) })
        : api<Expense>("/api/expenses", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: done,
  });
}

export function useDeleteExpense() {
  const done = useInvalidateMoney();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/expenses/${id}`, { method: "DELETE" }),
    onSuccess: done,
  });
}

export function useReview() {
  const done = useInvalidateMoney();
  return useMutation({
    mutationFn: ({ id, action, comment }: { id: number; action: "approve" | "reject"; comment?: string }) =>
      api<Expense>(`/api/approvals/${id}`, { method: "POST", body: JSON.stringify({ action, comment }) }),
    onSuccess: done,
  });
}
