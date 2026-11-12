import { useState } from "react";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import { getErrorMessage } from "../../services/apiClient";
import { KIND_LABELS, STATUS_LABELS } from "../../utils/formatters";
import { KINDS, STATUSES } from "./resourcesApi";

/**
 * Create (no `resource`) or edit. `kinds` = kinds the user may create;
 * `containers` = rooms/laboratories that equipment can be placed in.
 */
export default function ResourceForm({ resource, kinds = KINDS, containers, onSubmit, onCancel }) {
  const editing = Boolean(resource);
  const [form, setForm] = useState({
    kind: resource?.kind ?? kinds[0],
    name: resource?.name ?? "",
    code: resource?.code ?? "",
    status: resource?.status ?? "available",
    location: resource?.location ?? "",
    capacity: resource?.capacity ?? "",
    serial_number: resource?.serial_number ?? "",
    parent_id: String(resource?.parent_id ?? ""),
    description: resource?.description ?? "",
  });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [saving, setSaving] = useState(false);
  const isEquipment = form.kind === "equipment";

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    const found = {};
    if (!form.name.trim()) found.name = "Name is required";
    if (!form.code.trim()) found.code = "Code is required";
    if (form.capacity !== "" && !(Number(form.capacity) >= 1)) found.capacity = "Enter a number of 1 or more";
    setErrors(found);
    if (Object.keys(found).length) return;

    const payload = {
      name: form.name.trim(),
      code: form.code.trim(),
      status: form.status,
      location: form.location || null,
      description: form.description || null,
      capacity: !isEquipment && form.capacity !== "" ? Number(form.capacity) : null,
      serial_number: isEquipment ? form.serial_number || null : null,
      parent_id: isEquipment && form.parent_id ? Number(form.parent_id) : null,
    };
    if (!editing) payload.kind = form.kind;
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
      <div className="grid grid-cols-2 gap-3">
        <Select label="Type" name="kind" value={form.kind} onChange={onChange} disabled={editing}
          options={kinds.map((k) => ({ value: k, label: KIND_LABELS[k] }))} />
        <Select label="Status" name="status" value={form.status} onChange={onChange}
          options={STATUSES.map((s) => ({ value: s, label: STATUS_LABELS[s] }))} />
        <Input label="Name" name="name" value={form.name} onChange={onChange} error={errors.name} />
        <Input label="Code" name="code" placeholder="LAB-CS1" value={form.code} onChange={onChange} error={errors.code} />
        {isEquipment ? (
          <>
            <Input label="Serial number" name="serial_number" value={form.serial_number} onChange={onChange} />
            <Select label="Located in" name="parent_id" value={form.parent_id} onChange={onChange}
              options={containers.map((c) => ({ value: c.id, label: `${c.name} (${c.code})` }))} placeholder="— Shared / not in a room —" />
          </>
        ) : (
          <Input label="Capacity (seats)" name="capacity" type="number" min="1" value={form.capacity} onChange={onChange} error={errors.capacity} />
        )}
        <Input label="Location" name="location" value={form.location} onChange={onChange} className="col-span-2" />
      </div>
      <Input label="Description" name="description" value={form.description} onChange={onChange} />
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={saving}>{editing ? "Save" : "Create"}</Button>
      </div>
    </form>
  );
}
