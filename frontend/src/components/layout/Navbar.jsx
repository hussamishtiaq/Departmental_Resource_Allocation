import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { roleLabel } from "../../utils/formatters";
import Badge from "../ui/Badge";
import Button from "../ui/Button";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <span className="font-semibold text-slate-800">Department Resource System</span>
      <div className="flex items-center gap-3">
        <div className="text-right text-sm leading-tight">
          <div className="font-medium">{user.full_name}</div>
          <div className="text-slate-500">{user.email}</div>
        </div>
        <Badge tone="indigo">{roleLabel(user.role.name)}</Badge>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Log out"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          <LogOut size={16} /> Logout
        </Button>
      </div>
    </header>
  );
}
