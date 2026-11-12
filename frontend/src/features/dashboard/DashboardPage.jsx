import { Link } from "react-router-dom";
import PageHeader from "../../components/layout/PageHeader";
import { useAuth } from "../../hooks/useAuth";
import { roleLabel } from "../../utils/formatters";

export default function DashboardPage() {
  const { user, can } = useAuth();
  return (
    <>
      <PageHeader title={`Welcome, ${user.full_name}`} subtitle="Departmental Resource Allocation System" />
      <div className="grid max-w-2xl gap-4 sm:grid-cols-2">
        <Link to="/resources" className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow">
          <h2 className="font-semibold">Rooms, Labs & Equipment</h2>
          <p className="text-sm text-slate-500">Search availability and status{user.permissions.includes("resources:manage") ? ", and maintain records" : ""}.</p>
        </Link>
        <Link to="/hierarchy" className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow">
          <h2 className="font-semibold">Department Structure</h2>
          <p className="text-sm text-slate-500">Department → rooms/labs → equipment tree.</p>
        </Link>
        <Link to="/reservations" className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow">
          <h2 className="font-semibold">{can("reservations:review") ? "Reservations & Approvals" : "My Reservations"}</h2>
          <p className="text-sm text-slate-500">{can("reservations:review") ? "Approve requests and assign resources." : "Request a lab, room or equipment."}</p>
        </Link>
        {can("reservations:review") && (
          <Link to="/monitor" className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow">
            <h2 className="font-semibold">Resource Monitor</h2>
            <p className="text-sm text-slate-500">Who is using what right now.</p>
          </Link>
        )}
        {can("users:read") && (
          <Link to="/users" className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow">
            <h2 className="font-semibold">Users & Roles</h2>
            <p className="text-sm text-slate-500">Assign roles to department members.</p>
          </Link>
        )}
      </div>
      <p className="mt-6 text-sm text-slate-500">Signed in as <b>{roleLabel(user.role.name)}</b></p>
    </>
  );
}
