import apiClient from "../../services/apiClient";

export async function login(email, password) {
  // The API uses the OAuth2 password flow: form-encoded, `username` = email.
  const body = new URLSearchParams({ username: email, password });
  const { data } = await apiClient.post("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function register(payload) {
  const { data } = await apiClient.post("/auth/register", payload);
  return data;
}

export async function fetchMe() {
  const { data } = await apiClient.get("/auth/me");
  return data;
}
