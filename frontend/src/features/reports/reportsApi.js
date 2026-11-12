import apiClient from "../../services/apiClient";

export const fetchMonitor = async () => (await apiClient.get("/monitor")).data;
