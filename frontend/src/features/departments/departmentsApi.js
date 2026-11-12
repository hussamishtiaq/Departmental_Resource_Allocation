import apiClient from "../../services/apiClient";

export const fetchTree = async () => (await apiClient.get("/department/tree")).data;
export const updateDepartment = async (payload) => (await apiClient.put("/department", payload)).data;
