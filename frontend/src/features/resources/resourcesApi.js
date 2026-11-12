import apiClient from "../../services/apiClient";

export const KINDS = ["room", "laboratory", "equipment"];
export const STATUSES = ["available", "maintenance", "damaged", "retired"];

// Drop empty filter values so they are not sent as "?q=".
const clean = (params) => Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null));

export const fetchResources = async (params = {}) => (await apiClient.get("/resources", { params: clean(params) })).data;
export const fetchResource = async (id) => (await apiClient.get(`/resources/${id}`)).data;
export const createResource = async (payload) => (await apiClient.post("/resources", payload)).data;
export const updateResource = async (id, payload) => (await apiClient.patch(`/resources/${id}`, payload)).data;
export const deleteResource = async (id) => apiClient.delete(`/resources/${id}`);

/** Mirrors the server rule: lab staff manage equipment only. */
export function canManageKind(user, kind) {
  if (!user.permissions.includes("resources:manage")) return false;
  return !(user.role.name === "lab_staff" && kind !== "equipment");
}
