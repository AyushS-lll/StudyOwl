/**
 * StudyOwl typed API client.
 * All backend calls go through here — never use fetch() directly in components.
 */

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────

export interface StartSessionRequest {
  student_id: string;
  question: string;
  photo_b64?: string;
}

export interface StartSessionResponse {
  session_id: string;
  hint: string;
  hint_level: 1 | 2 | 3;
  subject: string;
}

export interface AttemptRequest {
  attempt_text: string;
}

export interface AttemptResponse {
  status: "correct" | "wrong";
  hint?: string;
  hint_level?: 1 | 2 | 3;
  message?: string;
}

export interface SubjectProgress {
  name: string;
  sessions: number;
  success_rate: number;
}

export interface StudentProgress {
  subjects: SubjectProgress[];
  recent_sessions: RecentSession[];
}

export interface RecentSession {
  id: string;
  question: string;
  subject: string;
  resolved: boolean;
  started_at: string;
  attempts_count: number;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem("studyowl_token");
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json() as Promise<T>;
}

// ── API calls ────────────────────────────────────────────────────────────────

export const api = {
  /** Start a new homework session and receive the first hint. */
  startSession: (body: StartSessionRequest) =>
    apiFetch<StartSessionResponse>("/api/session/start", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** Submit a student's answer attempt and receive the next hint or success. */
  submitAttempt: (sessionId: string, body: AttemptRequest) =>
    apiFetch<AttemptResponse>(`/api/session/${sessionId}/attempt`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** Fetch a student's progress data for the dashboard. */
  getProgress: (studentId: string) =>
    apiFetch<StudentProgress>(`/api/student/${studentId}/progress`),

  /** Login and store the JWT token. */
  login: async (email: string, password: string): Promise<void> => {
    const form = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/api/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) throw new Error("Login failed");
    const data = await res.json();
    localStorage.setItem("studyowl_token", data.access_token);
  },

  logout: () => localStorage.removeItem("studyowl_token"),
};
