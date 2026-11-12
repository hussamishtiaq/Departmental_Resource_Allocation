import { Plus, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import EmptyState from "../../components/feedback/EmptyState";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import Table from "../../components/ui/Table";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import { formatDateTime } from "../../utils/dateUtils";
import { RESERVATION_TONES } from "../../utils/formatters";
import { fetchResources } from "../resources/resourcesApi";
import { fetchUsers } from "../users/usersApi";
import ReservationForm from "./ReservationForm";
import * as api from "./reservationsApi";

export default function ReservationsPage() {
  const { user, can } = useAuth();
  const reviewer = can("reservations:review");
  const [status, setStatus] = useState("");
  const [mine, setMine] = useState(false);
  const [rows, setRows] = useState(null);
  const [resources, setResources] = useState([]);
  const [users, setUsers] = useState([]);
  const [dialog, setDialog] = useState(null); // "request" | "assign"
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(() => {
    api.fetchReservations({ status, mine: reviewer && mine })
      .then((d) => { setRows(d); setError(""); })
      .catch((e) => setError(getErrorMessage(e)));
  }, [status, mine, reviewer]);
  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    fetchResources({ status: "available", limit: 500 }).then(setResources).catch(() => {});
    if (can("reservations:assign")) fetchUsers().then(setUsers).catch(() => {});
  }, [can]);

  async function act(id, fn, note) {
    setBusyId(id);
    setError("");
    try { await fn(id, note); load(); } catch (e) { setError(getErrorMessage(e)); } finally { setBusyId(null); }
  }
  const askNote = (label) => window.prompt(`${label} (optional note)`, "") ?? null;

  const columns = [
    { key: "resource", header: "Resource", render: (r) => <div><div className="font-medium">{r.resource.name}</div><div className="text-xs text-slate-500">{r.resource.code}</div></div> },
    ...(reviewer ? [{ key: "user", header: "Requested by", render: (r) => <div><div>{r.user.full_name}</div><div className="text-xs text-slate-500">{r.user.email}</div></div> }] : []),
    { key: "when", header: "When", render: (r) => <div className="text-xs">{formatDateTime(r.start_time)}<br />→ {formatDateTime(r.end_time)}</div> },
    { key: "purpose", header: "Purpose", render: (r) => (r.purpose ?? "").replace("[demo] ", "") || "—" },
    { key: "status", header: "Status", render: (r) => (
      <div><Badge tone={RESERVATION_TONES[r.status]}>{r.status}</Badge>
        {r.review_note && <div className="mt-1 text-xs text-slate-500">“{r.review_note}”</div>}</div>
    ) },
    { key: "actions", header: "", render: (r) => {
      const isOwner = r.user.id === user.id;
      const open = r.status === "pending" || r.status === "approved";
      return (
        <div className="flex flex-wrap gap-1">
          {reviewer && r.status === "pending" && (<>
            <Button size="sm" disabled={busyId === r.id} onClick={() => act(r.id, api.approveReservation)}>Approve</Button>
            <Button size="sm" variant="secondary" disabled={busyId === r.id} onClick={() => act(r.id, api.rejectReservation, askNote("Reject"))}>Reject</Button>
          </>)}
          {open && (isOwner || reviewer) && (
            <Button size="sm" variant="ghost" disabled={busyId === r.id} onClick={() => act(r.id, api.cancelReservation, isOwner ? null : askNote("Cancel"))}>Cancel</Button>
          )}
        </div>
      );
    } },
  ];

  return (
    <>
      <PageHeader title={reviewer ? "Reservations & Approvals" : "My Reservations"}
        subtitle={reviewer ? "Review requests, assign resources and cancel bookings." : "Request rooms, laboratories and equipment."}
        actions={<>
          {can("reservations:assign") && <Button variant="secondary" onClick={() => setDialog("assign")}><UserPlus size={16} /> Assign resource</Button>}
          {can("reservations:create") && <Button onClick={() => setDialog("request")}><Plus size={16} /> New request</Button>}
        </>} />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Select aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)} placeholder="All statuses"
          options={["pending", "approved", "rejected", "cancelled"].map((s) => ({ value: s, label: s }))} />
        {reviewer && (
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} /> Only my own
          </label>
        )}
      </div>
      <ErrorMessage message={error} />
      {!rows ? <LoadingState /> : rows.length === 0 ? (
        <EmptyState title="No reservations" description="Requests you make will appear here." />
      ) : <Table columns={columns} rows={rows} />}

      <Modal open={Boolean(dialog)} title={dialog === "assign" ? "Assign a resource to a user" : "Request a resource"} onClose={() => setDialog(null)}>
        {dialog && (
          <ReservationForm mode={dialog} resources={resources} users={users} onCancel={() => setDialog(null)}
            onSubmit={async (payload) => {
              await (dialog === "assign" ? api.assignResource(payload) : api.requestReservation(payload));
              setDialog(null);
              load();
            }} />
        )}
      </Modal>
    </>
  );
}
