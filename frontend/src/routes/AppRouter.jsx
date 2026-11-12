import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "../components/layout/AppLayout";
import ProtectedRoute from "../components/layout/ProtectedRoute";
import LoginPage from "../features/auth/LoginPage";
import RegisterPage from "../features/auth/RegisterPage";
import DashboardPage from "../features/dashboard/DashboardPage";
import HierarchyPage from "../features/departments/HierarchyPage";
import ReportsPage from "../features/reports/ReportsPage";
import ReservationsPage from "../features/reservations/ReservationsPage";
import ResourceDetailsPage from "../features/resources/ResourceDetailsPage";
import ResourcesPage from "../features/resources/ResourcesPage";
import UsersPage from "../features/users/UsersPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/resources" element={<ResourcesPage />} />
            <Route path="/resources/:id" element={<ResourceDetailsPage />} />
            <Route path="/reservations" element={<ReservationsPage />} />
            <Route element={<ProtectedRoute permission="reservations:review" />}>
              <Route path="/monitor" element={<ReportsPage />} />
            </Route>
            <Route path="/hierarchy" element={<HierarchyPage />} />
            <Route element={<ProtectedRoute permission="users:read" />}>
              <Route path="/users" element={<UsersPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
