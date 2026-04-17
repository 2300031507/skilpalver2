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
    
    let body;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      body = await response.json();
    } else {
      const text = await response.text();
      console.error(`Non-JSON response for ${path}:`, text);
      throw new Error("Server returned an invalid response. Please check if the backend is running.");
    }

    if (!response.ok) {
      console.error(`API Error ${response.status}:`, body);
      throw new Error(body.detail || "Request failed");
    }
    return body;
  } catch (error) {
    console.error("Fetch network error:", error);
    throw error;
  }
}

// ── Auth (no token needed) ─────────────────────────────────

export async function signup(data) {
  try {
    const res = await fetch(`${BASE_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    
    let body;
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      body = await res.json();
    } else {
      const text = await res.text();
      console.error("Non-JSON signup response:", text);
      throw new Error("Server returned an invalid response. Please check if the backend is running.");
    }

    if (!res.ok) throw new Error(body.detail || "Signup failed");
    return body;
  } catch (error) {
    console.error("Signup error:", error);
    throw error;
  }
}

export async function login(email, password) {
  try {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    let body;
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      body = await res.json();
    } else {
      const text = await res.text();
      console.error("Non-JSON login response:", text);
      throw new Error("Server returned an invalid response. Please check if the backend is running.");
    }

    if (!res.ok) throw new Error(body.detail || "Login failed");
    // Store JWT
    setToken(body.access_token);
    return body;
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
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

export async function unlinkStudentProfile(universityId, studentId, platformSlug) {
  return request("/platforms/profile/unlink", {
    method: "POST",
    actorId: studentId,
    actorRole: "student",
    body: {
      university_id: universityId,
      student_id: studentId,
      platform_slug: platformSlug,
    },
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

