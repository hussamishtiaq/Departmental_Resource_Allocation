import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import LoadingState from "../feedback/LoadingState";

/** Requires login; optionally requires one of `roles` or a `permission`. */
export default function ProtectedRoute({ roles, permission }) {
  const { isAuthenticated, loading, hasRole, can } = useAuth();
  const location = useLocation();

  if (loading) return <LoadingState label="Checking session..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  if ((roles && !hasRole(...roles)) || (permission && !can(permission))) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}
