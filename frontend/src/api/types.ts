export type Status = "pending" | "approved" | "rejected";

export interface Me {
  id: number;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
  org_name: string;
  org_currency: string;
  plan: string;
  plan_limits: { can_export: boolean };
}

export interface Expense {
  id: number;
  employee_id: number;
  employee_name: string;
  category_id: number;
  category_name: string;
  amount: string;
  currency: string;
  spent_on: string;
  description: string;
  status: Status;
  review_comment: string | null;
}

export interface Category {
  id: number;
  name: string;
}

export interface Row {
  key: string;
  total: string;
  count: number;
}

export interface Dashboard {
  currency: string;
  approved_this_month: string;
  pending_total: string;
  pending_count: number;
  rejected_count: number;
  by_category: Row[];
}

export interface Report {
  currency: string;
  total: string;
  by_category: Row[];
  by_employee: Row[];
  by_month: Row[];
}

export interface Change {
  action: "update" | "status" | "delete";
  changed_by: string;
  changed_at: string;
  diff: Record<string, { old: unknown; new: unknown }>;
}
