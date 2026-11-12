import { ArrowLeft, CalendarPlus, Pencil, Trash2, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from "../../utils/formatters";
import ReservationForm from "../reservations/ReservationForm";
import * as resApi from "../reservations/reservationsApi";
import { fetchUsers } from "../users/usersApi";
import { formatDateTime } from "../../utils/dateUtils";
import ResourceForm from "./ResourceForm";
import * as api from "./resourcesApi";

export default function ResourceDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, can } = useAuth();
  const [reserving, setReserving] = useState(null); // "request" | "assign"
  const [schedule, setSchedule] = useState([]);
  const [users, setUsers] = useState([]);
  const [resource, setResource] = useState(null);
  const [containers, setContainers] = useState([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.fetchResource(id).then((r) => { setResource(r); setError(""); }).catch((e) => setError(getErrorMessage(e)));
  }, [id]);
  useEffect(() => { setResource(null); load(); }, [load]);
  useEffect(() => {
    resApi.fetchSchedule(id).then(setSchedule).catch(() => {});
    if (can("reservations:assign")) fetchUsers().then(setUsers).catch(() => {});
  }, [id, can, reserving]);
  useEffect(() => {
    api.fetchResources({ limit: 500 }).then((all) => setContainers(all.filter((r) => r.kind !== "equipment"))).catch(() => {});
  }, []);

  if (!resource) return error ? <ErrorMessage message={error} /> : <LoadingState />;
  const canEdit = api.canManageKind(user, resource.kind);

  async function changeStatus(status) {
    setBusy(true);
    try { await api.updateResource(resource.id, { status }); load(); }
    catch (e) { setError(getErrorMessage(e)); }
    finally { setBusy(false); }
  }

  return (
    <>
      <Link to="/resources" className="mb-3 inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
        <ArrowLeft size={14} /> All resources
      </Link>
      <PageHeader title={resource.name} subtitle={`${KIND_LABELS[resource.kind]} · ${resource.code}`}
        actions={(<>
          {resource.status === "available" && can("reservations:create") && (
            <Button onClick={() => setReserving("request")}><CalendarPlus size={14} /> Request</Button>)}
          {resource.status === "available" && can("reservations:assign") && (
            <Button variant="secondary" onClick={() => setReserving("assign")}><UserPlus size={14} /> Assign to user</Button>)}
          {canEdit && (<>
          <Button variant="secondary" onClick={() => setEditing(true)}><Pencil size={14} /> Edit</Button>
          <Button variant="danger" onClick={() => setConfirmDelete(true)}><Trash2 size={14} /> Delete</Button>
        </>)}</>)} />
      <ErrorMessage message={error} />
      <dl className="mb-6 grid max-w-xl grid-cols-[9rem_1fr] items-center gap-y-2 text-sm">
        <dt className="text-slate-500">Status</dt>
        <dd>{canEdit ? (
          <Select aria-label="Status" value={resource.status} disabled={busy} onChange={(e) => changeStatus(e.target.value)}
            options={api.STATUSES.map((s) => ({ value: s, label: STATUS_LABELS[s] }))} />
        ) : <Badge tone={STATUS_TONES[resource.status]}>{STATUS_LABELS[resource.status]}</Badge>}</dd>
        {resource.parent && (<><dt className="text-slate-500">Located in</dt>
          <dd><Link className="text-indigo-600 hover:underline" to={`/resources/${resource.parent.id}`}>{resource.parent.name}</Link></dd></>)}
        {resource.location && (<><dt className="text-slate-500">Location</dt><dd>{resource.location}</dd></>)}
        {resource.capacity != null && (<><dt className="text-slate-500">Capacity</dt><dd>{resource.capacity} seats</dd></>)}
        {resource.serial_number && (<><dt className="text-slate-500">Serial number</dt><dd>{resource.serial_number}</dd></>)}
        {resource.description && (<><dt className="text-slate-500">Description</dt><dd>{resource.description}</dd></>)}
      </dl>

      <h2 className="mb-2 text-lg font-semibold">Upcoming bookings</h2>
      {schedule.length === 0 ? <p className="mb-6 text-sm text-slate-500">No upcoming bookings.</p> : (
        <ul className="mb-6 max-w-xl divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {schedule.map((b, i) => <li key={i} className="px-4 py-2">{formatDateTime(b.start_time)} → {formatDateTime(b.end_time)}</li>)}
        </ul>
      )}

      {resource.kind !== "equipment" && (
        <>
          <h2 className="mb-2 text-lg font-semibold">Equipment in this {KIND_LABELS[resource.kind].toLowerCase()}</h2>
          {resource.children.length === 0 ? <p className="text-sm text-slate-500">No equipment assigned.</p> : (
            <ul className="max-w-xl divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {resource.children.map((c) => (
                <li key={c.id} className="flex items-center justify-between px-4 py-2 text-sm">
                  <Link to={`/resources/${c.id}`} className="font-medium text-indigo-600 hover:underline">{c.name} <span className="text-xs text-slate-500">{c.code}</span></Link>
                  <Badge tone={STATUS_TONES[c.status]}>{STATUS_LABELS[c.status]}</Badge>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      <Modal open={editing} title="Edit resource" onClose={() => setEditing(false)}>
        {editing && (
          <ResourceForm resource={resource} kinds={[resource.kind]} containers={containers} onCancel={() => setEditing(false)}
            onSubmit={async (payload) => { await api.updateResource(resource.id, payload); setEditing(false); load(); }} />
        )}
      </Modal>
      <Modal open={Boolean(reserving)} title={reserving === "assign" ? "Assign to a user" : "Request this resource"} onClose={() => setReserving(null)}>
        {reserving && (
          <ReservationForm mode={reserving} resources={[resource]} users={users} resourceId={resource.id}
            onCancel={() => setReserving(null)}
            onSubmit={async (payload) => {
              await (reserving === "assign" ? resApi.assignResource(payload) : resApi.requestReservation(payload));
              setReserving(null);
              navigate("/reservations");
            }} />
        )}
      </Modal>
      <ConfirmDialog open={confirmDelete} loading={busy} message={`Delete "${resource.name}"?`}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={async () => {
          setBusy(true);
          try { await api.deleteResource(resource.id); navigate("/resources"); }
          catch (e) { setError(getErrorMessage(e)); setConfirmDelete(false); setBusy(false); }
        }} />
    </>
  );
}
