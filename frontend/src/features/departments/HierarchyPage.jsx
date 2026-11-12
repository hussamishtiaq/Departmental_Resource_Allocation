import { Building2, FlaskConical, Pencil, Wrench, DoorOpen } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from "../../utils/formatters";
import * as api from "./departmentsApi";

const ICONS = { room: DoorOpen, laboratory: FlaskConical, equipment: Wrench };

function Node({ node }) {
  const Icon = ICONS[node.kind];
  return (
    <li>
      <Link to={`/resources/${node.id}`} className="flex items-center gap-2 rounded-md px-3 py-1.5 hover:bg-slate-50">
        <Icon size={15} className="text-slate-500" />
        <span className="font-medium">{node.name}</span>
        <span className="text-xs text-slate-500">{node.code}</span>
        <Badge tone="blue">{KIND_LABELS[node.kind]}</Badge>
        {node.status !== "available" && <Badge tone={STATUS_TONES[node.status]}>{STATUS_LABELS[node.status]}</Badge>}
        {node.children.length > 0 && <span className="text-xs text-slate-400">{node.children.length} item(s)</span>}
      </Link>
      {node.children.length > 0 && (
        <ul className="ml-6 border-l border-slate-200 pl-2">
          {node.children.map((c) => <Node key={c.id} node={c} />)}
        </ul>
      )}
    </li>
  );
}

/** Department -> rooms / laboratories -> equipment. */
export default function HierarchyPage() {
  const { can } = useAuth();
  const [tree, setTree] = useState(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", description: "" });
  const [saving, setSaving] = useState(false);

  const load = () => api.fetchTree().then(setTree).catch((e) => setError(getErrorMessage(e)));
  useEffect(() => { load(); }, []);

  async function save(e) {
    e.preventDefault();
    if (form.name.trim().length < 2) return setError("Name is required");
    setSaving(true);
    try {
      await api.updateDepartment({ name: form.name.trim(), code: form.code.trim(), description: form.description || null });
      setEditing(false);
      setError("");
      await load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (!tree) return error ? <ErrorMessage message={error} /> : <LoadingState />;
  const assigned = tree.children.filter((c) => c.kind !== "equipment");
  const shared = tree.children.filter((c) => c.kind === "equipment");

  return (
    <>
      <PageHeader title="Department Structure"
        subtitle="Department → rooms and laboratories → equipment. Click an item to open it."
        actions={can("department:manage") && (
          <Button variant="secondary" onClick={() => { setForm({ name: tree.name, code: tree.code, description: tree.description ?? "" }); setEditing(true); }}>
            <Pencil size={14} /> Edit department
          </Button>
        )} />
      <ErrorMessage message={error} />
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-2 flex items-center gap-2 text-lg font-semibold">
          <Building2 size={18} /> {tree.name} <span className="text-sm font-normal text-slate-500">{tree.code}</span>
        </div>
        {tree.description && <p className="mb-2 text-sm text-slate-500">{tree.description}</p>}
        {tree.children.length === 0 ? (
          <p className="text-sm text-slate-500">No rooms, laboratories or equipment yet.</p>
        ) : (
          <ul className="ml-3 border-l border-slate-200 pl-2">
            {assigned.map((n) => <Node key={n.id} node={n} />)}
            {shared.length > 0 && (
              <li className="mt-2">
                <div className="px-3 py-1 text-xs font-medium uppercase tracking-wide text-slate-400">Shared equipment (not in a room)</div>
                <ul className="ml-3 border-l border-slate-200 pl-2">{shared.map((n) => <Node key={n.id} node={n} />)}</ul>
              </li>
            )}
          </ul>
        )}
      </div>

      <Modal open={editing} title="Edit department" onClose={() => setEditing(false)}>
        <form onSubmit={save} className="space-y-3">
          <Input label="Name" name="name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Code" name="code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <Input label="Description" name="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditing(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
