/**
 * StudyOwl typed API client.
 * All backend calls go through here — never use fetch() directly in components.
 */

const BASE = import.meta.env.VITE_API_URL ?? "";

// ── Types ────────────────────────────────────────────────────────────────────

export interface SignUpRequest {
  name: string;
  email: string;
  password: string;
  grade_level: string;
  role?: "student" | "teacher";
}

export interface LoginRequest {
  email: string;
  password: string;
  role: "student" | "teacher";
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: "student" | "teacher";
}

export interface StartSessionRequest {
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

export interface LearningResource {
  title: string;
  url?: string;
  summary?: string;
}

export interface AttemptResponse {
  status: "correct" | "wrong";
  hint?: string;
  hint_level?: 1 | 2 | 3;
  message?: string;
  final_answer?: string;
  review_mode?: boolean;
  review_url?: string;
  learning_resources?: LearningResource[];
}

export interface SubjectProgress {
  name: string;
  sessions: number;
  success_rate: number;
}

export interface RecentSession {
  id: string;
  question: string;
  subject: string;
  resolved: boolean;
  started_at: string;
}

export interface StudentProgress {
  subjects: SubjectProgress[];
  recent_sessions: RecentSession[];
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem("studyowl_token");
  const isAuthRequest = path.startsWith("/api/") && !path.startsWith("/api/auth");

  if (isAuthRequest && !token) {
    throw new Error("Authentication token missing. Please log in again.");
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((init?.headers as Record<string, string>) ?? {}),
  };

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json() as Promise<T>;
}

// ── API calls ────────────────────────────────────────────────────────────────

export const api = {
  /** Sign up a new account. */
  signup: async (body: SignUpRequest): Promise<TokenResponse> => {
    const result = await apiFetch<TokenResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify(body),
    });
    localStorage.setItem("studyowl_token", result.access_token);
    return result;
  },

  /** Log in and store the JWT token. */
  login: async (body: LoginRequest): Promise<TokenResponse> => {
    const result = await apiFetch<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
    localStorage.setItem("studyowl_token", result.access_token);
    return result;
  },

  /** Fetch students list for teachers. */
  getStudentList: () =>
    apiFetch<{ students: Array<{ id: string; name: string; grade_level: string }> }>(
      "/api/student/list"
    ),

  /** Fetch a specific student's progress. */
  getStudentProgress: (studentId: string) =>
    apiFetch<StudentProgress>(`/api/student/${studentId}/progress`),

  /** Log out by removing token. */
  logout: () => {
    localStorage.removeItem("studyowl_token");
  },

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

  /** Fetch teacher classroom analytics and alert metrics. */
  getTeacherMetrics: () =>
    apiFetch<{ total_students: number; sessions_today: number; average_success_rate: number; pending_alerts: number }>(
      "/api/alert/metrics"
    ),

  /** Fetch current active alerts for teachers. */
  getAlerts: () => apiFetch<{ pending_alerts: Array<{ id: string; student_name: string; question: string; hint_level: number; fails_at_level: number; started_at: string }> }>(
      "/api/alert"
    ),
};

