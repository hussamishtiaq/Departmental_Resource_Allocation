import { Activity, Boxes, CalendarCheck, Network, LayoutDashboard, Users } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/resources", label: "Resources", icon: Boxes },
  { to: "/reservations", label: "Reservations", icon: CalendarCheck },
  { to: "/monitor", label: "Monitor", icon: Activity, permission: "reservations:review" },
  { to: "/hierarchy", label: "Department Structure", icon: Network },
  { to: "/users", label: "Users", icon: Users, permission: "users:read" },
];

export default function Sidebar() {
  const { can } = useAuth();
  return (
    <nav className="w-56 shrink-0 border-r border-slate-200 bg-white p-3">
      <ul className="space-y-1">
        {LINKS.filter((l) => !l.permission || can(l.permission)).map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
