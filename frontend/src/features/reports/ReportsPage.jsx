import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import LoadingState from "../../components/feedback/LoadingState";
import PageHeader from "../../components/layout/PageHeader";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { getErrorMessage } from "../../services/apiClient";
import { formatDateTime } from "../../utils/dateUtils";
import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from "../../utils/formatters";
import * as api from "./reportsApi";

const REFRESH_MS = 30000;

function Stat({ label, value, tone = "text-slate-900" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className={`text-2xl font-bold ${tone}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function Section({ title, empty, items, render }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <h2 className="border-b border-slate-100 px-4 py-2 font-semibold">{title}</h2>
      {items.length === 0 ? <p className="px-4 py-3 text-sm text-slate-500">{empty}</p> : (
        <ul className="divide-y divide-slate-100 text-sm">{items.map(render)}</ul>
      )}
    </section>
  );
}

/** Live monitor: who is using what now, what is coming, what needs attention. */
export default function ReportsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.fetchMonitor().then((d) => { setData(d); setError(""); }).catch((e) => setError(getErrorMessage(e)));
  }, []);
  useEffect(() => {
    load();
    const t = setInterval(load, REFRESH_MS); // auto-refresh
    return () => clearInterval(t);
  }, [load]);

  if (!data) return error ? <ErrorMessage message={error} /> : <LoadingState />;
  const s = data.summary;
  const who = (r) => <><b>{r.resource.name}</b> <span className="text-xs text-slate-500">{r.resource.code}</span> · {r.user.full_name}</>;

  return (
    <>
      <PageHeader title="Resource Monitor" subtitle={`Updated ${formatDateTime(data.generated_at)} · refreshes every 30 s`}
        actions={<Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>} />
      <ErrorMessage message={error} />
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Total resources" value={s.total_resources} />
        <Stat label="Available" value={s.available} tone="text-green-700" />
        <Stat label="In use right now" value={s.in_use_now} tone="text-indigo-700" />
        <Stat label="Pending requests" value={s.pending_requests} tone="text-amber-700" />
        <Stat label="Starting in 24 h" value={s.starting_next_24h} />
        <Stat label="Under maintenance" value={s.maintenance} tone="text-amber-700" />
        <Stat label="Damaged" value={s.damaged} tone="text-red-700" />
        <Stat label="Retired" value={s.retired} tone="text-slate-500" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="In use right now" empty="Nothing is booked at the moment." items={data.in_use_now}
          render={(r) => <li key={r.id} className="px-4 py-2">{who(r)}<div className="text-xs text-slate-500">until {formatDateTime(r.end_time)}</div></li>} />
        <Section title="Starting in the next 24 hours" empty="No bookings coming up." items={data.upcoming}
          render={(r) => <li key={r.id} className="px-4 py-2">{who(r)}<div className="text-xs text-slate-500">{formatDateTime(r.start_time)} → {formatDateTime(r.end_time)}</div></li>} />
        <Section title="Waiting for approval" empty="No pending requests." items={data.pending}
          render={(r) => <li key={r.id} className="px-4 py-2">{who(r)}<div className="text-xs text-slate-500">{formatDateTime(r.start_time)} → {formatDateTime(r.end_time)}</div></li>} />
        <Section title="Needs attention" empty="Everything is in working order." items={data.needs_attention}
          render={(r) => (
            <li key={r.id} className="flex items-center justify-between px-4 py-2">
              <Link to={`/resources/${r.id}`} className="text-indigo-600 hover:underline">{r.name} <span className="text-xs text-slate-500">{r.code} · {KIND_LABELS[r.kind]}</span></Link>
              <Badge tone={STATUS_TONES[r.status]}>{STATUS_LABELS[r.status]}</Badge>
            </li>)} />
      </div>
      <p className="mt-4 text-sm text-slate-500">Approve pending requests on the <Link to="/reservations" className="text-indigo-600 hover:underline">Reservations</Link> page.</p>
    </>
  );
}
