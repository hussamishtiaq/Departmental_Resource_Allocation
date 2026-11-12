import { useCallback, useEffect, useState } from "react";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import { roleLabel } from "../../utils/formatters";
import * as api from "./usersApi";

export default function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(() => {
    api.fetchUsers().then(setUsers).catch((e) => setError(getErrorMessage(e)));
  }, []);
  useEffect(() => { load(); }, [load]);

  // The hierarchy: you may only manage people below you (HOD: anyone).
  const mine = me.assignable_roles;
  const canTouch = (u) => u.id !== me.id && (me.role.name === "hod" || mine.includes(u.role.name));

  async function change(u, payload) {
    setBusyId(u.id);
    setError("");
    try {
      const updated = await api.updateUser(u.id, payload);
      setUsers((list) => list.map((x) => (x.id === u.id ? updated : x)));
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  const columns = [
    { key: "full_name", header: "Name", render: (u) => <div><div className="font-medium">{u.full_name}</div><div className="text-xs text-slate-500">{u.email}</div></div> },
    { key: "role", header: "Role", render: (u) => canTouch(u) ? (
      <Select aria-label={`Role of ${u.full_name}`} value={u.role.name} disabled={busyId === u.id}
        onChange={(e) => change(u, { role: e.target.value })}
        options={[...new Set([u.role.name, ...mine])].map((r) => ({ value: r, label: roleLabel(r), disabled: !mine.includes(r) }))} />
    ) : <Badge tone="indigo">{roleLabel(u.role.name)}</Badge> },
    { key: "is_active", header: "Status", render: (u) => canTouch(u) ? (
      <Button size="sm" variant={u.is_active ? "secondary" : "primary"} disabled={busyId === u.id}
        onClick={() => change(u, { is_active: !u.is_active })}>{u.is_active ? "Deactivate" : "Activate"}</Button>
    ) : <Badge tone={u.is_active ? "green" : "red"}>{u.is_active ? "active" : "disabled"}</Badge> },
  ];

  return (
    <>
      <PageHeader title="Users" subtitle="Assign roles following the hierarchy: HOD › Department Admin › Lab Staff › Faculty › Student." />
      <ErrorMessage message={error} />
      {users ? <Table columns={columns} rows={users} /> : <LoadingState />}
    </>
  );
}
