import apiClient from "../../services/apiClient";

const clean = (params) => Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null && v !== false));

export const fetchReservations = async (params = {}) => (await apiClient.get("/reservations", { params: clean(params) })).data;
export const requestReservation = async (payload) => (await apiClient.post("/reservations", payload)).data;
export const assignResource = async (payload) => (await apiClient.post("/reservations/assign", payload)).data;
export const fetchSchedule = async (resourceId) => (await apiClient.get(`/reservations/schedule/${resourceId}`)).data;
export const approveReservation = async (id, note) => (await apiClient.post(`/reservations/${id}/approve`, { note })).data;
export const rejectReservation = async (id, note) => (await apiClient.post(`/reservations/${id}/reject`, { note })).data;
export const cancelReservation = async (id, note) => (await apiClient.post(`/reservations/${id}/cancel`, { note })).data;
