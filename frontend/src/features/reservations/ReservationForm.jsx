import { useEffect, useState } from "react";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import { getErrorMessage } from "../../services/apiClient";
import { defaultLocalInput, formatDateTime, localInputToIso } from "../../utils/dateUtils";
import { KIND_LABELS } from "../../utils/formatters";
import * as api from "./reservationsApi";

/**
 * Request a resource (mode="request") or allocate it to someone (mode="assign",
 * needs `users`). `resources` = bookable resources; `resourceId` pre-selects one.
 */
export default function ReservationForm({ mode = "request", resources, users = [], resourceId, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    resource_id: String(resourceId ?? ""),
    user_id: "",
    start: defaultLocalInput(1),
    end: defaultLocalInput(3),
    purpose: "",
  });
  const [busy, setBusy] = useState([]);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [saving, setSaving] = useState(false);

  const onChange = (e) => { setApiError(""); setForm({ ...form, [e.target.name]: e.target.value }); };

  // Show what is already booked so the user can pick a free slot.
  useEffect(() => {
    if (!form.resource_id) return setBusy([]);
    let ignore = false;
    api.fetchSchedule(form.resource_id).then((s) => !ignore && setBusy(s)).catch(() => {});
    return () => { ignore = true; };
  }, [form.resource_id]);

  async function submit(e) {
    e.preventDefault();
    const found = {};
    if (!form.resource_id) found.resource_id = "Choose a resource";
    if (mode === "assign" && !form.user_id) found.user_id = "Choose a user";
    if (!form.start) found.start = "Required";
    if (!form.end) found.end = "Required";
    if (form.start && form.end && new Date(form.end) <= new Date(form.start)) found.end = "Must be after the start";
    if (form.start && new Date(form.start) < new Date(Date.now() - 60000)) found.start = "Start is in the past";
    setErrors(found);
    if (Object.keys(found).length) return;

    const payload = {
      resource_id: Number(form.resource_id),
      start_time: localInputToIso(form.start),
      end_time: localInputToIso(form.end),
      purpose: form.purpose || null,
    };
    if (mode === "assign") payload.user_id = Number(form.user_id);
    setSaving(true);
    try {
      await onSubmit(payload);
    } catch (err) {
      setApiError(getErrorMessage(err));
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      <ErrorMessage message={apiError} />
      <Select label="Resource" name="resource_id" value={form.resource_id} onChange={onChange} disabled={Boolean(resourceId)}
        placeholder="Select a room, lab or equipment" error={errors.resource_id}
        options={resources.map((r) => ({ value: r.id, label: `${r.name} (${KIND_LABELS[r.kind]}) ${r.code}` }))} />
      {mode === "assign" && (
        <Select label="Assign to" name="user_id" value={form.user_id} onChange={onChange} placeholder="Select a user" error={errors.user_id}
          options={users.filter((u) => u.is_active).map((u) => ({ value: u.id, label: `${u.full_name} (${u.email})` }))} />
      )}
      <div className="grid grid-cols-2 gap-3">
        <Input label="From" name="start" type="datetime-local" value={form.start} onChange={onChange} error={errors.start} />
        <Input label="Until" name="end" type="datetime-local" value={form.end} onChange={onChange} error={errors.end} />
      </div>
      <Input label="Purpose" name="purpose" placeholder="e.g. Programming lab class" value={form.purpose} onChange={onChange} />
      {busy.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
          <div className="font-medium">Already booked:</div>
          {busy.map((b, i) => <div key={i}>{formatDateTime(b.start_time)} → {formatDateTime(b.end_time)}</div>)}
        </div>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={saving}>{mode === "assign" ? "Assign" : "Send request"}</Button>
      </div>
    </form>
  );
}
