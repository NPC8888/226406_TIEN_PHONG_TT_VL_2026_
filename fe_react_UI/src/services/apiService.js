const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const AUTH_TOKEN_KEY = "INTENER_AUTH_TOKEN";

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY);
export const setAuthToken = (token) => localStorage.setItem(AUTH_TOKEN_KEY, token);
export const clearAuthToken = () => localStorage.removeItem(AUTH_TOKEN_KEY);
export const getGoogleLoginUrl = (nextPath = "/") => {
  const params = new URLSearchParams({ next: nextPath });
  return `${API_BASE_URL}/auth/google/login?${params.toString()}`;
};

const buildHeaders = (auth = true) => {
  const headers = {
    "Content-Type": "application/json",
  };
  const token = getAuthToken();
  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail || body?.message || response.statusText || "Lỗi mạng";
    throw new Error(message);
  }
  return response.json();
};

export const postJsonData = async (endpoint, data, auth = false, method = "POST") => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers: buildHeaders(auth),
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Error posting JSON data:", error);
    throw error;
  }
};

export const fetchJsonData = async (endpoint, auth = false) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: buildHeaders(auth),
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Error fetching JSON data:", error);
    throw error;
  }
};

export const generatePosts = async (postData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/generate-content`, {
      method: "POST",
      headers: buildHeaders(Boolean(getAuthToken())),
      body: JSON.stringify(postData),
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Error generating posts:", error);
    throw error;
  }
};

export const estimateGeneratePosts = async (postData) => postJsonData("/generate-content/estimate", postData, true);

export const suggestWritingStyles = async (payload, signal) => {
  try {
    const response = await fetch(`${API_BASE_URL}/writing-style-suggestions`, {
      method: "POST",
      headers: buildHeaders(Boolean(getAuthToken())),
      body: JSON.stringify(payload),
      signal,
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Error suggesting writing styles:", error);
    throw error;
  }
};

export const suggestSectionOutlines = async (payload) => {
  try {
    const response = await fetch(`${API_BASE_URL}/section-outline-suggestions`, {
      method: "POST",
      headers: buildHeaders(Boolean(getAuthToken())),
      body: JSON.stringify(payload),
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Error suggesting section outlines:", error);
    throw error;
  }
};

export const loginUser = async (payload) => postJsonData("/auth/login", payload, false);
export const registerUser = async (payload) => postJsonData("/auth/register", payload, false);
export const getProfile = async () => fetchJsonData("/auth/me", true);
export const listPlans = async () => fetchJsonData("/plans", false);
export const purchasePlan = async (planSlug) => postJsonData("/subscriptions/purchase", { plan_slug: planSlug }, true);
export const getActiveSubscription = async () => fetchJsonData("/subscriptions/active", true);
export const getCreditBalance = async () => fetchJsonData("/credits/balance", true);
export const getHistory = async () => fetchJsonData("/posts/history", true);
export const getAdminDashboard = async (params = {}) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ""));
  return fetchJsonData(`/admin/dashboard${query.toString() ? `?${query.toString()}` : ""}`, true);
};
export const loginAdmin = async (payload) => postJsonData("/admin/login", payload, false);
export const getAdminEnvSettings = async () => fetchJsonData("/admin/env-settings", true);
export const updateAdminEnvSettings = async (items) => postJsonData("/admin/env-settings", { items }, true, "PUT");
export const updateModelPricing = async (modelKey, payload) =>
  postJsonData(`/admin/model-pricing/${encodeURIComponent(modelKey)}`, payload, true, "PUT");
export const getAdminPostDetail = async (postId) => fetchJsonData(`/admin/posts/${postId}`, true);
export const listGeminiModels = async () => fetchJsonData("/admin/gemini/models", true);
export const testGeminiKey = async (payload) => postJsonData("/admin/gemini/test-key", payload, true);

export const submitPostForm = (url, fields) => {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = url;
  form.style.display = "none";

  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value ?? "";
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
};
