import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./lib/auth";
import Login from "./pages/Login";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const MyExpenses = lazy(() => import("./pages/MyExpenses"));
const Approvals = lazy(() => import("./pages/Approvals"));
const Reports = lazy(() => import("./pages/Reports"));

function Guard({ perm, children }: { perm?: string; children: ReactNode }) {
  const { me, loading, can } = useAuth();
  if (loading) return null;
  if (!me) return <Navigate to="/login" replace />;
  if (perm && !can(perm)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <Guard>
              <Layout />
            </Guard>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="expenses" element={<Guard perm="submit_expense"><MyExpenses /></Guard>} />
          <Route path="approvals" element={<Guard perm="review_expense"><Approvals /></Guard>} />
          <Route path="reports" element={<Guard perm="view_reports"><Reports /></Guard>} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
