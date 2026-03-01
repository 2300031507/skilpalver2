const BASE_URL = "/api";

// ── Token management ───────────────────────────────────────

function getToken() {
  return localStorage.getItem("access_token") || "";
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

// ── Generic request helper ─────────────────────────────────

async function request(path, options = {}) {
  try {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };

    // Use JWT Bearer if available, fallback to header-based auth
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    } else {
      headers["X-Actor-Id"] = options.actorId || "S001";
      headers["X-Actor-Role"] = options.actorRole || "student";
    }

    const fetchOptions = {
      method: options.method || "GET",
      headers,
    };
    if (options.body) {
      fetchOptions.body = JSON.stringify(options.body);
    }
    const response = await fetch(`${BASE_URL}${path}`, fetchOptions);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      console.error(`API Error ${response.status}:`, errData);
      throw new Error(errData.detail || "Request failed");
    }
    return response.json();
  } catch (error) {
    console.error("Fetch network error:", error);
    throw error;
  }
}

// ── Auth (no token needed) ─────────────────────────────────

export async function signup(data) {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Signup failed");
  return body;
}

export async function login(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Login failed");
  // Store JWT
  setToken(body.access_token);
  return body;
}

// ── Dashboard ──────────────────────────────────────────────

export async function fetchStudentDashboard(actorId, universityId = "UNI001") {
  return request(`/dashboard/student?university_id=${universityId}`, {
    actorId,
    actorRole: "student",
  });
}

export async function fetchTeacherDashboard(actorId, universityId = "UNI001", page = 1) {
  return request(`/dashboard/teacher?university_id=${universityId}&page=${page}`, {
    actorId,
    actorRole: "teacher",
  });
}

export async function fetchNotifications(actorId, role) {
  return request("/notifications", { actorId, actorRole: role });
}

// ── Platform Config (admin) ────────────────────────────────

export async function fetchPlatformRegistry() {
  return request("/platforms/registry", { actorRole: "admin", actorId: "ADMIN" });
}

export async function fetchPlatformConfig(universityId) {
  return request(`/platforms/config/${universityId}`, {
    actorRole: "admin",
    actorId: "ADMIN",
  });
}

export async function savePlatformConfig(universityId, platforms) {
  return request("/platforms/config", {
    method: "PUT",
    actorRole: "admin",
    actorId: "ADMIN",
    body: { university_id: universityId, platforms },
  });
}

// ── Student Platform Profiles ──────────────────────────────

export async function fetchStudentProfiles(universityId, studentId) {
  return request(`/platforms/profile/${universityId}/${studentId}`, {
    actorId: studentId,
    actorRole: "student",
  });
}

export async function linkStudentProfiles(universityId, studentId, profiles) {
  return request("/platforms/profile/link", {
    method: "POST",
    actorId: studentId,
    actorRole: "student",
    body: { university_id: universityId, student_id: studentId, profiles },
  });
}

// ── Bulk Operations (admin) ────────────────────────────────

export async function bulkLinkProfiles(universityId, rows) {
  return request("/platforms/profile/bulk-link", {
    method: "POST",
    actorRole: "admin",
    actorId: "ADMIN",
    body: { university_id: universityId, rows },
  });
}

