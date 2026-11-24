const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("auth_token") || "";
}

export function setToken(token) {
  localStorage.setItem("auth_token", token);
}

export function clearToken() {
  localStorage.removeItem("auth_token");
  invalidateCache();
  window.dispatchEvent(new Event("auth:logout"));
}

export async function login(username, password) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Incorrect username or password");
  }
  const data = await res.json();
  if (data.token) {
    setToken(data.token);
  }
  return data;
}

async function getAuthHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Client-side In-memory Cache ──────────────────────────────────────────────
const cache = new Map();
const DEFAULT_TTL_MS = 30000; // 30 seconds default cache

export function invalidateCache(prefix) {
  if (!prefix) {
    cache.clear();
    return;
  }
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) {
      cache.delete(key);
    }
  }
}

function autoInvalidate(path) {
  const segments = path.split("/").filter(Boolean);
  if (segments.length >= 2) {
    const base = `/${segments[0]}/${segments[1]}`;
    invalidateCache(base);
  }
  // Any mutation potentially affects dashboard summary
  invalidateCache("/api/dashboard");
}

async function fetchWithAuth(path, options = {}) {
  let headers = await getAuthHeaders();
  let res = await fetch(`${API}${path}`, {
    ...options,
    headers: { ...options.headers, ...headers },
  });

  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized. Please log in again.");
  }

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/**
 * apiGet with automatic memory caching
 * @param {string} path - API endpoint
 * @param {Object} [options]
 * @param {number} [options.maxAge=30000] - Cache TTL in ms (0 to bypass cache)
 * @param {boolean} [options.force=false] - If true, bypasses cache and updates it
 */
export async function apiGet(path, options = {}) {
  const maxAge = options.maxAge ?? DEFAULT_TTL_MS;
  const force = options.force ?? false;

  if (!force && maxAge > 0) {
    const cached = cache.get(path);
    if (cached && Date.now() - cached.timestamp < maxAge) {
      return cached.data;
    }
  }

  const data = await fetchWithAuth(path);
  if (maxAge > 0) {
    cache.set(path, { timestamp: Date.now(), data });
  }
  return data;
}

export async function apiPost(path, body) {
  const res = await fetchWithAuth(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  autoInvalidate(path);
  return res;
}

export async function apiDelete(path, body) {
  const res = await fetchWithAuth(path, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  autoInvalidate(path);
  return res;
}

export async function apiPut(path, body) {
  const res = await fetchWithAuth(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  autoInvalidate(path);
  return res;
}

export async function apiPatch(path, body) {
  const res = await fetchWithAuth(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  autoInvalidate(path);
  return res;
}

export async function apiUpload(path, file, extras = {}) {
  let headers = await getAuthHeaders();
  const fd = new FormData();
  fd.append("file", file);
  for (const [k, v] of Object.entries(extras)) {
    fd.append(k, v);
  }

  let res = await fetch(`${API}${path}`, { method: "POST", headers, body: fd });
  if (res.status === 401) {
    clearToken();
    throw new Error("Unauthorized. Please log in again.");
  }

  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  autoInvalidate(path);
  return data;
}

export function chartUrl(name, period = "month") {
  const token = getToken();
  if (name === "period") {
    return `${API}/api/finance/charts/period?period=${period}&t=${Date.now()}&token=${token}`;
  }
  return `${API}/api/finance/charts/${name}?t=${Date.now()}&token=${token}`;
}
