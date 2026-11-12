import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import EmptyState from "../../components/feedback/EmptyState";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from "../../utils/formatters";
import ResourceForm from "./ResourceForm";
import * as api from "./resourcesApi";

export default function ResourcesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ q: "", kind: "", status: "" });
  const [query, setQuery] = useState(filters); // debounced copy that triggers fetches
  const [resources, setResources] = useState(null);
  const [containers, setContainers] = useState([]);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const creatableKinds = api.KINDS.filter((k) => api.canManageKind(user, k));

  useEffect(() => {
    api.fetchResources({ limit: 500 })
      .then((all) => setContainers(all.filter((r) => r.kind !== "equipment")))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setQuery(filters), 300);
    return () => clearTimeout(t);
  }, [filters]);

  useEffect(() => {
    let ignore = false;
    api.fetchResources(query)
      .then((data) => { if (!ignore) { setResources(data); setError(""); } })
      .catch((e) => { if (!ignore) setError(getErrorMessage(e)); });
    return () => { ignore = true; };
  }, [query]);

  const onChange = (e) => setFilters({ ...filters, [e.target.name]: e.target.value });

  const columns = [
    { key: "name", header: "Name", render: (r) => (
      <div><div className="font-medium">{r.name}</div><div className="text-xs text-slate-500">{r.code}</div></div>
    ) },
    { key: "kind", header: "Type", render: (r) => <Badge tone="blue">{KIND_LABELS[r.kind]}</Badge> },
    { key: "place", header: "Where", render: (r) => r.parent ? r.parent.name : (r.location || "—") },
    { key: "capacity", header: "Capacity", render: (r) => r.capacity ?? "—" },
    { key: "status", header: "Status", render: (r) => <Badge tone={STATUS_TONES[r.status]}>{STATUS_LABELS[r.status]}</Badge> },
  ];

  return (
    <>
      <PageHeader title="Rooms, Laboratories & Equipment" subtitle="Inventory of the department's resources."
        actions={creatableKinds.length > 0 && <Button onClick={() => setCreating(true)}><Plus size={16} /> Add resource</Button>} />
      <div className="mb-4 grid gap-3 rounded-lg border border-slate-200 bg-white p-3 sm:grid-cols-3">
        <Input name="q" placeholder="Search name, code, serial" aria-label="Search" value={filters.q} onChange={onChange} />
        <Select name="kind" aria-label="Type" value={filters.kind} onChange={onChange} placeholder="All types"
          options={api.KINDS.map((k) => ({ value: k, label: KIND_LABELS[k] }))} />
        <Select name="status" aria-label="Status" value={filters.status} onChange={onChange} placeholder="Any status"
          options={Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label }))} />
      </div>
      <ErrorMessage message={error} />
      {!resources ? <LoadingState /> : resources.length === 0 ? (
        <EmptyState title="No resources found" description="Try changing the filters." />
      ) : (
        <Table columns={columns} rows={resources} onRowClick={(r) => navigate(`/resources/${r.id}`)} />
      )}
      <Modal open={creating} title="Add resource" onClose={() => setCreating(false)}>
        {creating && (
          <ResourceForm kinds={creatableKinds} containers={containers} onCancel={() => setCreating(false)}
            onSubmit={async (payload) => { const r = await api.createResource(payload); navigate(`/resources/${r.id}`); }} />
        )}
      </Modal>
    </>
  );
}
