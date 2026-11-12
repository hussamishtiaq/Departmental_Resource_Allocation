import apiClient from "../../services/apiClient";

export const fetchUsers = async () => (await apiClient.get("/users")).data;
export const updateUser = async (id, payload) => (await apiClient.patch(`/users/${id}`, payload)).data;
