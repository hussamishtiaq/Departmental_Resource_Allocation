export const formatDateTime = (iso) =>
  iso ? new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "—";

/** <input type="datetime-local"> value -> ISO string with timezone (what the API requires). */
export const localInputToIso = (value) => new Date(value).toISOString();

/** Default value for a datetime-local input: next full hour + offset. */
export function defaultLocalInput(addHours = 1) {
  const d = new Date();
  d.setMinutes(0, 0, 0);
  d.setHours(d.getHours() + addHours);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
